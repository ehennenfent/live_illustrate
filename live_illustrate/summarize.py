from datetime import datetime
from openai import OpenAI

from .util import AsyncThread

SYSTEM_PROMPT = "You are a helpful assistant that describes scenes to an artist who wants to draw them. \
You will be given several lines of dialogue that contain details about the physical surroundings of the characters. \
Your job is to summarize the details of the scene in a bulleted list containing 4-7 bullet points. \
If there is more than one scene described by the dialog, summarize only the most recent one. \
Remember to be concise and not include details that cannot be seen."


class TextSummarizer(AsyncThread):
    def __init__(self, model: str) -> None:
        super().__init__()
        self.openai_client: OpenAI = OpenAI()
        self.model: str = model

    def work(self, text: str) -> str:
        start = datetime.now()
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
        print("[INFO] Summarized in", datetime.now() - start)
        return [choice.message.content.strip() for choice in response.choices][-1]
