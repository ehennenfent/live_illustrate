from datetime import datetime

from openai import OpenAI

from .util import AsyncThread

QUALITY = "standard"
EXTRA = "digital painting, fantasy art"


class ImageRenderer(AsyncThread):
    def __init__(self, model: str, image_size: str) -> None:
        super().__init__()
        self.openai_client: OpenAI = OpenAI()
        self.model: str = model
        self.size: str = image_size

    def work(self, text: str) -> str:
        start = datetime.now()
        rendered = self.openai_client.images.generate(
            model=self.model, prompt=text + "\n" + EXTRA, size=self.size, quality=QUALITY, n=1
        ).data[0]
        print("[INFO] Rendered in", datetime.now() - start)
        return rendered.url
