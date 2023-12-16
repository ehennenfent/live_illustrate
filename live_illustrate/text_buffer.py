import typing as t
from datetime import datetime
from time import sleep

from .util import AsyncThread, get_last_n_tokens, num_tokens_from_string


class TextBuffer(AsyncThread):
    def __init__(self, wait_minutes: float, max_context: int, persistence: float = 1.0) -> None:
        super().__init__("TextBuffer")
        self.buffer: t.List[str] = []
        self.wait_seconds: int = int(wait_minutes * 60)
        self.max_context: int = max_context
        self.persistence: float = persistence

    def work(self, next_text: str) -> int:
        """Very simple, just puts the text in the buffer. The real work is done in buffer_forever."""
        self.buffer.append(next_text)
        return len(self.buffer)

    def get_context(self) -> str:
        """Grabs the last max_context tokens from the buffer. If persistence < 1, trims it down
        to at most persistence * 100 %"""
        context = "\n".join(get_last_n_tokens(self.buffer, self.max_context))
        if self.persistence < 1.0:
            self.buffer = get_last_n_tokens(
                self.buffer, int(self.persistence * num_tokens_from_string("\n".join(self.buffer)))
            )
        return context

    def buffer_forever(self, callback: t.Callable[[str], t.Any]) -> None:
        """every wait_seconds, grabs the last max_context tokens and sends them off to the
        summarizer (via `callback`)"""
        last_run = datetime.now()
        while True:
            if (datetime.now() - last_run).seconds > self.wait_seconds:
                last_run = datetime.now()
                callback(self.get_context())
            sleep(1)
