import logging
import typing as t
from abc import abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from queue import Queue
from time import sleep

import tiktoken


@dataclass
class Transcription:
    transcription: str


@dataclass
class Summary(Transcription):
    summary: str

    @classmethod
    def from_transcription(cls, transcription: Transcription, summary: str) -> "Summary":
        return cls(transcription.transcription, summary)


@dataclass
class Image(Summary):
    image_url: str

    @classmethod
    def from_summary(cls, summary: Summary, image_url: str) -> "Image":
        return cls(summary.transcription, summary.summary, image_url)


@lru_cache(maxsize=2)
def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Use OpenAI's tokenizer to count the number of tokens"""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_last_n_tokens(buffer: t.List[str], n: int) -> t.List[str]:
    """Conservatively grabs the last n-ish tokens worth of lines from the buffer. Will undershoot."""
    if not buffer:
        return []
    context: t.List[str] = []
    for line in reversed(buffer):
        if num_tokens_from_string("\n".join(context) + "\n" + line) > n:
            break
        context.append(line)
    return [c for c in reversed(context)]


def is_transcription_interesting(transcription: Transcription) -> bool:
    """Whisper likes to sometimes just output a series of dots and spaces, which are boring"""
    return len(transcription.transcription.replace(".", "").replace(" ", "").strip()) > 0


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
