import typing as t
from collections import deque
from datetime import datetime
from time import sleep

from .util import AsyncThread, num_tokens_from_string


class TextBuffer(AsyncThread):
    def __init__(self, wait_minutes: float, max_context: int) -> None:
        super().__init__()
        self.buffer: t.List[str] = []
        self.wait_seconds: int = int(wait_minutes * 60)
        self.max_context: int = max_context

    def work(self, next_text: str) -> None:
        self.buffer.append(next_text)

    def get_last_n_tokens(self, n: int) -> str:
        if not self.buffer:
            return ""
        my_copy = deque(self.buffer)
        context = [my_copy.pop()]
        while (num_tokens_from_string("\n".join(context))) < self.max_context:
            if not my_copy:
                break
            context.append(my_copy.pop())
        return "\n".join(reversed(context[:-1]))

    def buffer_forever(self, callback: t.Callable[[str], t.Any]) -> None:
        last_run = datetime.now()
        while True:
            if (datetime.now() - last_run).seconds > self.wait_seconds:
                last_run = datetime.now()
                callback(self.get_last_n_tokens(self.max_context))
            sleep(1)
