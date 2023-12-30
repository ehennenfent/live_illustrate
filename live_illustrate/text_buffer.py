import typing as t
from datetime import datetime
from time import sleep

from .util import AsyncThread, Transcription, get_last_n_tokens, num_tokens_from_string


class TextBuffer(AsyncThread):
    def __init__(self, wait_minutes: float, max_context: int, persistence: float = 1.0) -> None:
        super().__init__("TextBuffer")
        self.buffer: t.List[Transcription] = []
        self.wait_seconds: int = int(wait_minutes * 60)
        self.max_context: int = max_context
        self.persistence: float = persistence

    def work(self, next_transcription: Transcription) -> int:
        """Very simple, just puts the text in the buffer. The real work is done in buffer_forever."""
        self.buffer.append(next_transcription)
        return len(self.buffer)

    def get_context(self) -> Transcription:
        """Grabs the last max_context tokens from the buffer. If persistence < 1, trims it down
        to at most persistence * 100 %"""
        as_text = [t.transcription for t in self.buffer]
        context = Transcription("\n".join(get_last_n_tokens(as_text, self.max_context)))
        if self.persistence < 1.0:
            self.buffer = [
                Transcription(line)
                for line in get_last_n_tokens(
                    as_text, int(self.persistence * num_tokens_from_string("\n".join(as_text)))
                )
            ]
        return context

    def buffer_forever(self, callback: t.Callable[[Transcription], t.Any]) -> None:
        """every wait_seconds, grabs the last max_context tokens and sends them off to the
        summarizer (via `callback`)"""
        last_run = datetime.now()
        while True:
            if (datetime.now() - last_run).seconds > self.wait_seconds:
                last_run = datetime.now()
                callback(self.get_context())
            sleep(1)
