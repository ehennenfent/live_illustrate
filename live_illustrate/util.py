import typing as t
from abc import abstractmethod
from functools import lru_cache
from queue import Queue
from time import sleep

import tiktoken


@lru_cache(maxsize=2)
def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_last_n_tokens(buffer: t.List[str], n: int) -> t.List[str]:
    if not buffer:
        return []
    context: t.List[str] = []
    for line in reversed(buffer):
        if num_tokens_from_string("\n".join(context) + "\n" + line) > n:
            break
        context.append(line)
    return [c for c in reversed(context)]


class AsyncThread:
    SLEEP_TIME = 0.25

    def __init__(self) -> None:
        self.queue: Queue[t.Any] = Queue()

    @abstractmethod
    def work(self, *args) -> t.Any:
        raise NotImplementedError()

    def start(self, callback) -> None:
        while True:
            if not self.queue.empty():
                callback(self.work(*self.queue.get()))
            sleep(self.SLEEP_TIME)

    def send(self, *args) -> None:
        self.queue.put(args)
