from base64 import b64decode
from datetime import datetime

from openai import OpenAI

from .prompts import IMAGE_EXTENSION, PromptManager
from .util import AsyncThread, Image, Summary


class ImageRenderer(AsyncThread):
    def __init__(self, model: str, image_size: str, image_quality: str, image_style: str) -> None:
        super().__init__("ImageRenderer")
        self.openai_client: OpenAI = OpenAI()
        self.model: str = model
        self.size: str = image_size
        self.image_quality: str = image_quality
        self.image_style: str = image_style
        self.prompt_manager = PromptManager()

    def work(self, summary: Summary) -> Image | None:
        """Sends the text to OpenAI, spits out an Image"""
        start = datetime.now()
        data = self.openai_client.images.generate(
            model=self.model,
            prompt=summary.summary + "\n" + self.prompt_manager.get_prompt(IMAGE_EXTENSION),
            size=self.size,  # type: ignore[arg-type]
            # quality=self.image_quality,  # type: ignore[arg-type]
            # style=self.image_style,  # type: ignore[arg-type]
            response_format="b64_json",
            n=1,
        ).data
        if data is None:
            self.logger.warning("No data returned from OpenAI")
            return None
        rendered = data[0]
        self.logger.info("Rendered in %s", datetime.now() - start)

        return Image.from_summary(summary, b64decode(rendered.b64_json)) if rendered.b64_json is not None else None
