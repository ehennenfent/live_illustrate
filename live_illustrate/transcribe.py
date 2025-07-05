import typing as t
from time import time_ns

import speech_recognition as sr

from .util import AsyncThread, Transcription

# TODO - might want to figure out how to lower the pause detection threshold.
# Our party talks a lot.
DYNAMIC_ENERGY_THRESHOLD = True
SAMPLE_RATE = 16000


def _get_duration_millis(audio: sr.AudioData) -> int:
    return int(len(audio.frame_data) / (audio.sample_rate * audio.sample_width) * 1000)


class AudioTranscriber(AsyncThread):
    def __init__(
        self, model: str, phrase_timeout: float, audio_callback: t.Callable[[sr.AudioData], None] | None = None
    ) -> None:
        super().__init__("AudioTranscriber")

        self.recorder = sr.Recognizer()
        self.source = sr.Microphone(sample_rate=SAMPLE_RATE)
        self.model = model
        self.phrase_timeout = int(phrase_timeout * 60)

        self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD
        self.recorder.operation_timeout = self.phrase_timeout * 2.5

        self.audio_callback = audio_callback

    def work(self, _, audio_data: sr.AudioData) -> Transcription:
        """Passes audio data to whisper, spits text back out"""
        audio_duration = _get_duration_millis(audio_data)
        start_millis = time_ns() // 1_000_000
        transcribed = self.recorder.recognize_whisper(
            audio_data,
            model=self.model,
            language="english",
        ).strip()
        return Transcription.with_timestamps(
            transcription=transcribed,
            start_millis=start_millis,
            transcription_time=(time_ns() // 1_000_000 - start_millis),
            audio_duration=audio_duration,
        )

    def start(self, callback: t.Callable[[str], None]) -> None:
        with self.source:
            print("Adjusting for ambient noise... ", end="", flush=True)
            self.recorder.adjust_for_ambient_noise(self.source, duration=2)
            print("Done!", flush=True)
        # This creates a separate thread for the audio recording,
        # but it's non-blocking, so we just let it live here
        self.recorder.listen_in_background(self.source, self.on_audio_chunk, phrase_time_limit=self.phrase_timeout)

        super().start(callback)

    def on_audio_chunk(self, context, audio_data: sr.AudioData) -> None:
        if self.audio_callback is not None:
            self.audio_callback(audio_data)
        self.send(context, audio_data)
