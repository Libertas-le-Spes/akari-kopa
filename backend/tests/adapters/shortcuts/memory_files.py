from pathlib import Path


class MemoryFiles:
    def __init__(self):
        self.texts: dict[Path, str] = {}
        self.written: list[tuple[Path, str | None]] = []

    def exists(self, path: Path) -> bool:
        return path in self.texts

    def read(self, path: Path) -> str:
        return self.texts[path]

    def write_whole(self, path: Path, text: str, was: str | None) -> None:
        self.written.append((path, was))
        self.texts[path] = text

    def remove(self, path: Path) -> None:
        self.texts.pop(path, None)
