from datetime import datetime

from openai import OpenAI

from .util import AsyncThread

# Hacky, but an easy way to get slightly more consistent results
EXTRA = "digital painting, fantasy art"


class ImageRenderer(AsyncThread):
    def __init__(self, model: str, image_size: str, image_quality: str, image_style: str) -> None:
        super().__init__("ImageRenderer")
        self.openai_client: OpenAI = OpenAI()
        self.model: str = model
        self.size: str = image_size
        self.image_quality: str = image_quality
        self.image_style: str = image_style

    def work(self, text: str) -> str | None:
        """Sends the text to Dall-e, spits out an image URL"""
        start = datetime.now()
        rendered = self.openai_client.images.generate(
            model=self.model,
            prompt=text + "\n" + EXTRA,
            size=self.size,
            quality=self.image_quality,
            style=self.image_style,
            n=1,
        ).data[0]
        self.logger.info("Rendered in %s", datetime.now() - start)
        return rendered.url
