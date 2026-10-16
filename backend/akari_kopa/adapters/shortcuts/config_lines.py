from pathlib import Path


class ConfigLines:
    def __init__(self, path: Path):
        self.path = path

    def exists(self) -> bool:
        return self.path.is_file()

    def has(self, fragment: str) -> bool:
        return self.exists() and any(fragment in line for line in self._lines())

    def add(self, line: str) -> None:
        text = self.path.read_text(encoding="utf-8")
        self.path.write_text(text + ("" if text.endswith("\n") or not text else "\n") + line + "\n", encoding="utf-8")

    def remove(self, fragment: str) -> None:
        kept = [line for line in self._lines() if fragment not in line]
        self.path.write_text("".join(kept), encoding="utf-8")

    def _lines(self) -> list[str]:
        return self.path.read_text(encoding="utf-8").splitlines(keepends=True)
