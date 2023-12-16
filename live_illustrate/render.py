from openai import OpenAI

from .util import AsyncThread

SIZE = "1792x1024"
QUALITY = "standard"


class ImageRenderer(AsyncThread):
    def __init__(self, model: str) -> None:
        super().__init__()
        self.openai_client: OpenAI = OpenAI()
        self.model: str = model

    def work(self, text: str) -> str:
        rendered = self.openai_client.images.generate(
            model=self.model, prompt=text, size=SIZE, quality=QUALITY, n=1
        ).data[0]

        return rendered.url
