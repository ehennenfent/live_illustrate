from datetime import datetime
from pathlib import Path

import requests


class SessionData:
    def __init__(self, data_dir: Path, echo: bool = True) -> None:
        self.start_time = datetime.now()

        self.data_dir: Path = data_dir.joinpath(self.start_time.strftime("%Y_%m_%d-%H_%M_%S"))
        self.echo: bool = echo

    def save_image(self, url: str) -> None:
        try:
            r = requests.get((url), stream=True)
            if r.status_code == 200:
                with open(self.data_dir.joinpath(f"{self._time_since}.png"), "wb") as outf:
                    for chunk in r:
                        outf.write(chunk)
        except Exception as e:
            print("failed to save image to file:", e)

    def save_summary(self, text: str):
        try:
            with open(self.data_dir.joinpath(f"{self._time_since}.txt"), "w") as summaryf:
                print(text, file=summaryf)
        except Exception as e:
            print("failed to write summary to file:", e)

    def save_transcription(self, text: str):
        try:
            with open(self.data_dir.joinpath("transcript.txt"), "a") as transf:
                if self.echo:
                    print(self._time_since, ">", text)
                print(self._time_since, ">", text, file=transf, flush=True)
        except Exception as e:
            print("failed to write transcript to file:", e)

    @property
    def _time_since(self) -> str:
        delta = datetime.now() - self.start_time
        minutes, seconds = divmod(delta.seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return f"{hours}h_{minutes:02}m_{seconds:02}s"

    def __enter__(self) -> "SessionData":
        if not (parent := self.data_dir.parent).exists():
            parent.mkdir()
        self.data_dir.mkdir()
        return self

    def __exit__(self, *exc) -> None:
        pass
