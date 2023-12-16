from abc import abstractmethod
from queue import Queue
from time import sleep

import tiktoken


def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


class AsyncThread:
    SLEEP_TIME = 0.25

    def __init__(self) -> None:
        self.queue = Queue()

    @abstractmethod
    def work(self, *args):
        raise NotImplementedError()

    def start(self, callback):
        while True:
            if not self.queue.empty():
                callback(self.work(*self.queue.get()))
            sleep(self.SLEEP_TIME)

    def send(self, *args):
        self.queue.put(args)
