import logging
import os
from datetime import datetime
from pathlib import Path

import requests
from discord import File, SyncWebhook

from .util import Image, Summary, Transcription

DISCORD_WEBHOOK = "DISCORD_WEBHOOK"


class SessionData:
    """Creates a data/<timestamp> folder for the session and stores images, summaries, and transcripts"""

    def __init__(self, data_dir: Path, echo: bool = True) -> None:
        self.start_time = datetime.now()
        self.logger = logging.getLogger("SessionData")

        self.data_dir: Path = data_dir.joinpath(self.start_time.strftime("%Y_%m_%d-%H_%M_%S"))
        self.echo: bool = echo

        self.discord_webhook: str | None = os.getenv(DISCORD_WEBHOOK)
        if self.discord_webhook is not None:
            self.logger.info("Discord upload is enabled")

    def save_image(self, image: Image) -> None:
        try:
            r = requests.get((image.image_url), stream=True)
            if r.status_code == 200:
                fname = self.data_dir.joinpath(f"{self._time_since}.png")
                with open(fname, "wb") as outf:
                    for chunk in r:
                        outf.write(chunk)
        except Exception as e:
            self.logger.error("failed to save image to file: %s", e)
        else:
            try:
                if self.discord_webhook is not None:
                    with open(fname, "rb") as image_file:
                        SyncWebhook.from_url(self.discord_webhook).send(
                            file=File(image_file, description=image.summary[:1023])
                        )
            except Exception as e:
                self.logger.error("failed to send image to discord: %s", e)

    def save_summary(self, summary: Summary) -> None:
        """saves the provided text to its own file"""
        try:
            with open(self.data_dir.joinpath(f"{self._time_since}.txt"), "w") as summaryf:
                print(summary.summary, file=summaryf)
        except Exception as e:
            self.logger.error("failed to write summary to file: %s", e)

    def save_transcription(self, transcription: Transcription) -> None:
        """appends the provided text to the transcript file"""
        try:
            with open(self.data_dir.joinpath("transcript.txt"), "a") as transf:
                if self.echo:
                    print(self._time_since, ">", transcription.transcription)
                print(self._time_since, ">", transcription.transcription, file=transf, flush=True)
        except Exception as e:
            self.logger.error("failed to write transcript to file: %s", e)

    @property
    def _time_since(self) -> str:
        delta = datetime.now() - self.start_time
        minutes, seconds = divmod(delta.seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return f"{hours}h_{minutes:02}m_{seconds:02}s"

    def __enter__(self) -> "SessionData":  # create the directories upon entry, not upon init
        if not (parent := self.data_dir.parent).exists():
            parent.mkdir()
        self.data_dir.mkdir()
        return self

    def __exit__(self, *exc) -> None:
        pass
