import typing as t
from pathlib import Path

PROMPTS_FOLDER = Path(__file__).parent.joinpath("prompts")
IMAGE_EXTENSION = PROMPTS_FOLDER.joinpath("image_extra.txt")
SUMMARY = PROMPTS_FOLDER.joinpath("summary.txt")


class PromptManager:
    def __init__(self):
        self.cached: t.Dict[Path, str] = {}
        self.last_modified = {}

    def get_prompt(self, path: Path) -> str:
        last_modified = path.stat().st_mtime
        if self.last_modified.get(path) != last_modified:
            with open(path, "r") as f:
                self.cached[path] = f.read()
            self.last_modified[path] = last_modified
        return self.cached[path]
