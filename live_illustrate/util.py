import logging
import typing as t
import wave
from abc import abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from queue import Queue
from statistics import mean, stdev
from time import sleep

import requests
import speech_recognition as sr
import tiktoken

# Whisper's favorite phrase is "thank you", followed closely by "thanks for watching!".
# We might miss legit transcriptions this way, but the frequency with which these phrases show up
# without other dialogue is very low compared to the frequency with which whisper imagines them.
TRANSCRIPTION_HALLUCINATIONS = ["Thank you.", "Thanks for watching!", "I'm sorry."]


@dataclass
class Transcription:
    transcription: str
    start_millis: int

    @classmethod
    def with_timestamps(
        cls, transcription: str, start_millis: int, transcription_time: int, audio_duration: t.Optional[int] = None
    ) -> "Transcription":
        instance = cls(transcription, start_millis)
        # clunkier than `=`, but doesn't set off mypy
        setattr(instance, "transcription_time", transcription_time)
        setattr(instance, "audio_duration", audio_duration)
        return instance


@dataclass
class Summary(Transcription):
    summary: str

    @classmethod
    def from_transcription(cls, transcription: Transcription, summary: str) -> "Summary":
        return cls(transcription.transcription, transcription.start_millis, summary)


@dataclass
class Image(Summary):
    image_bytes: bytes

    @classmethod
    def from_summary(cls, summary: Summary, image_bytes: bytes) -> "Image":
        return cls(summary.transcription, summary.start_millis, summary.summary, image_bytes)


@lru_cache(maxsize=2)
def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Use OpenAI's tokenizer to count the number of tokens"""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_last_n_tokens(buffer: t.List[Transcription], n: int) -> t.List[Transcription]:
    """Conservatively grabs the last n-ish tokens worth of lines from the buffer. Will undershoot."""
    if not buffer:
        return []
    context: t.List[Transcription] = []
    for line in reversed(buffer):
        if num_tokens_from_string("\n".join(t.transcription for t in context) + "\n" + line.transcription) > n:
            break
        context.append(line)
    return [c for c in reversed(context)]


def is_transcription_interesting(transcription: Transcription) -> bool:
    """If Whisper doesn't hear anything, it will sometimes emit predictable nonsense."""

    # Sometimes we just get a sequence of dots and spaces.
    is_not_empty = len(transcription.transcription.replace(".", "").replace(" ", "").strip()) > 0

    # Sometimes we get a phrase from TRANSCRIPTION_HALLUCINATIONS (see above)
    is_not_hallucination = all(
        len(transcription.transcription.replace(maybe_hallucination, "").replace(" ", "").strip()) > 0
        for maybe_hallucination in TRANSCRIPTION_HALLUCINATIONS
    )

    return is_not_empty and is_not_hallucination


class AsyncThread:
    """Generic thread that has a work queue and a callback to run on the result"""

    SLEEP_TIME = 0.25
    MAX_ERRORS = 5

    def __init__(self, logger_name="AsyncThread") -> None:
        self.queue: Queue[t.Any] = Queue()
        self._consecutive_errors: int = 0
        self.logger = logging.getLogger(logger_name)

    @abstractmethod
    def work(self, *args) -> t.Any:
        raise NotImplementedError()

    def start(self, callback) -> None:
        while True:
            if not self.queue.empty():
                if self.queue.qsize() > 25:
                    self.logger.warning("%d items are backed up in the queue", self.queue.qsize())
                try:
                    callback(self.work(*self.queue.get()))
                    self._consecutive_errors = 0
                except Exception as e:
                    self._consecutive_errors += 1
                    self.logger.error(e)
                    if self._consecutive_errors > self.MAX_ERRORS:
                        self.logger.critical("Abandoning execution after %d consecutive errors", self.MAX_ERRORS)
                        exit(-1)
            sleep(self.SLEEP_TIME)

    def send(self, *args) -> None:
        self.queue.put(args)


def download_image(url: str) -> bytes:
    r = requests.get((url), stream=True)
    out = bytes()
    if r.status_code == 200:
        for chunk in r:
            out += chunk
    return out


def mean_and_stdev(data: t.Any) -> tuple[float, float]:
    values = list(data)
    return (mean(values), stdev(values)) if len(values) > 1 else (0.0, 0.0)


def audiodata_from_file(path: Path) -> sr.AudioData:
    with wave.open(str(path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()
        frame_data = wav_file.readframes(wav_file.getnframes())
        return sr.AudioData(frame_data=frame_data, sample_rate=sample_rate, sample_width=sample_width)
