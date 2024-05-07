from datetime import datetime

from openai import OpenAI

from .prompts import SUMMARY, PromptManager
from .util import AsyncThread, Summary, Transcription, num_tokens_from_string


class TextSummarizer(AsyncThread):
    def __init__(self, model: str) -> None:
        super().__init__("TextSummarizer")
        self.openai_client: OpenAI = OpenAI()
        self.model: str = model
        self.prompt_manager = PromptManager()

    def work(self, transcription: Transcription) -> Summary | None:
        """Sends the big buffer of provided text to ChatGPT, returns bullets describing the setting"""
        text = transcription.transcription
        if (token_count := num_tokens_from_string(text)) == 0:
            self.logger.info("No tokens in transcription, skipping summarization")
            return None

        start = datetime.now()
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.prompt_manager.get_prompt(SUMMARY)},
                {"role": "user", "content": text},
            ],
        )
        self.logger.info("Summarized %d tokens in %s", token_count, datetime.now() - start)
        if response.choices:
            return [
                (
                    Summary.from_transcription(transcription, content.strip())
                    if (content := choice.message.content)
                    else None
                )
                for choice in response.choices
            ][-1]
        return None
