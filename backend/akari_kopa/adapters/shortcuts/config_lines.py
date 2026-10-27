from pathlib import Path

from akari_kopa.adapters.shortcuts.text_files import TextFiles


class ConfigLines:
    def __init__(self, path: Path, files: TextFiles):
        self.path = path
        self.files = files

    def exists(self) -> bool:
        return self.files.exists(self.path)

    def has(self, fragment: str) -> bool:
        if not self.exists():
            return False
        for line in self._lines(self.files.read(self.path)):
            if fragment in line:
                return True
        return False

    def add(self, line: str) -> None:
        text = self.files.read(self.path)
        self.files.write_whole(self.path, _ending_a_line(text) + line + "\n", was=text)

    def remove(self, fragment: str) -> None:
        text = self.files.read(self.path)
        kept = []
        for line in self._lines(text):
            if fragment not in line:
                kept.append(line)
        self.files.write_whole(self.path, "".join(kept), was=text)

    def _lines(self, text: str) -> list[str]:
        return text.splitlines(keepends=True)


def _ending_a_line(text: str) -> str:
    if not text or text.endswith("\n"):
        return text
    return text + "\n"
