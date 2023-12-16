from openai import OpenAI

from .util import AsyncThread

QUALITY = "standard"


class ImageRenderer(AsyncThread):
    def __init__(self, model: str, image_size=str) -> None:
        super().__init__()
        self.openai_client: OpenAI = OpenAI()
        self.model: str = model
        self.size = image_size

    def work(self, text: str) -> str:
        rendered = self.openai_client.images.generate(
            model=self.model, prompt=text, size=self.size, quality=QUALITY, n=1
        ).data[0]

        return rendered.url
