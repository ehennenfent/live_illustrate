import typing as t
from datetime import datetime
from time import sleep

from .util import AsyncThread, Transcription, get_last_n_tokens, num_tokens_from_string


class TextBuffer(AsyncThread):
    def __init__(self, wait_minutes: float, max_context: int, persistence: float = 1.0) -> None:
        super().__init__("TextBuffer")
        self._buffer: t.List[Transcription] = []
        self.wait_seconds: int = int(wait_minutes * 60)
        self.max_context: int = max_context
        self.persistence: float = persistence

    def work(self, next_transcription: Transcription) -> int:
        """Very simple, just puts the text in the buffer. The real work is done in buffer_forever."""
        self._buffer.append(next_transcription)
        return len(self._buffer)

    def get_context(self) -> Transcription:
        """Grabs the last max_context tokens from the buffer. If persistence < 1, trims it down
        to at most persistence * 100 %"""
        # Since we're getting context infrequently, we'll sort before doing so rather than
        # using a priority queue (which are needlessly stupid in Python).
        self._buffer.sort(key=lambda t: t.start_millis)
        insert_into_context = get_last_n_tokens(self._buffer, self.max_context)
        context = Transcription(
            "\n".join(t.transcription for t in insert_into_context),
            start_millis=insert_into_context[0].start_millis if insert_into_context else 0,
        )
        if self.persistence < 1.0:
            self._buffer = get_last_n_tokens(self._buffer, int(self.persistence * self.total_tokens))
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

    @property
    def total_tokens(self) -> int:
        return num_tokens_from_string("\n".join(t.transcription for t in self._buffer))
