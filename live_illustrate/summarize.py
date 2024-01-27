from datetime import datetime

from openai import OpenAI

from .util import AsyncThread, Summary, Transcription, num_tokens_from_string

SYSTEM_PROMPT = "You are a helpful assistant that describes scenes to an artist who wants to draw them. \
You will be given several lines of dialogue that contain details about the physical surroundings of the characters. \
Your job is to summarize the details of the scene in a bulleted list containing 4-7 bullet points. \
If there is more than one scene described by the dialog, summarize only the most recent one. \
Remember to be concise and not include details that cannot be seen."  # Not so good about this last bit, eh?


class TextSummarizer(AsyncThread):
    def __init__(self, model: str) -> None:
        super().__init__("TextSummarizer")
        self.openai_client: OpenAI = OpenAI()
        self.model: str = model

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
                {"role": "system", "content": SYSTEM_PROMPT},
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
