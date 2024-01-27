import typing as t

import speech_recognition as sr  # type: ignore

from .util import AsyncThread, Transcription

# TODO - might want to figure out how to lower the pause detection threshold.
# Our party talks a lot.
DYNAMIC_ENERGY_THRESHOLD = True
SAMPLE_RATE = 16000


class AudioTranscriber(AsyncThread):
    def __init__(self, model: str, phrase_timeout: float) -> None:
        super().__init__("AudioTranscriber")

        self.recorder = sr.Recognizer()
        self.source = sr.Microphone(sample_rate=SAMPLE_RATE)
        self.model = model
        self.phrase_timeout = int(phrase_timeout * 60)

        self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD

    def work(self, _, audio_data) -> Transcription:
        """Passes audio data to whisper, spits text back out"""
        return Transcription(self.recorder.recognize_whisper(audio_data, model=self.model).strip())

    def start(self, callback: t.Callable[[str], None]) -> None:
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        # This creates a separate thread for the audio recording,
        # but it's non-blocking, so we just let it live here
        self.recorder.listen_in_background(self.source, self.send, phrase_time_limit=self.phrase_timeout)

        super().start(callback)
