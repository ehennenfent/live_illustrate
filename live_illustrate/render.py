import typing as t
from datetime import datetime

from openai import OpenAI

from .util import AsyncThread, Image, Summary

# Prompt engineering level 1,000,000
EXTRA: t.List[str] = ["digital painting, fantasy art"]


class ImageRenderer(AsyncThread):
    def __init__(self, model: str, image_size: str, image_quality: str, image_style: str) -> None:
        super().__init__("ImageRenderer")
        self.openai_client: OpenAI = OpenAI()
        self.model: str = model
        self.size: str = image_size
        self.image_quality: str = image_quality
        self.image_style: str = image_style

    def work(self, summary: Summary) -> Image | None:
        """Sends the text to Dall-e, spits out an image URL"""
        start = datetime.now()
        rendered = self.openai_client.images.generate(
            model=self.model,
            prompt="\n".join((summary.summary, *EXTRA)),
            size=self.size,  # type: ignore[arg-type]
            quality=self.image_quality,  # type: ignore[arg-type]
            style=self.image_style,  # type: ignore[arg-type]
            n=1,
        ).data[0]
        self.logger.info("Rendered in %s", datetime.now() - start)
        return Image.from_summary(summary, rendered.url) if rendered.url is not None else None
