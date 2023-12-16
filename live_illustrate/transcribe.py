import typing as t

import speech_recognition as sr

from .util import AsyncThread

DYNAMIC_ENERGY_THRESHOLD = True
SAMPLE_RATE = 16000


class AudioTranscriber(AsyncThread):
    def __init__(self, model: str) -> None:
        super().__init__()

        self.recorder = sr.Recognizer()
        self.source = sr.Microphone(sample_rate=SAMPLE_RATE)
        self.model = model

        self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD

    def work(self, audio_data) -> str:
        return self.recorder.recognize_whisper(audio_data, model=self.model).strip()

    def start(self, callback: t.Callable[[str], None]) -> None:
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
            self.recorder.listen_in_background(self.source, self.send)

        super().start(callback)
