import os
import secrets
from pathlib import Path

from akari_kopa.use_cases.shortcut.ports import ShortcutRefused

NEW_FILE = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
NEW_FILE_MODE = 0o644


class TextFiles:
    def exists(self, path: Path) -> bool:
        return path.is_file()

    def read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def write_whole(self, path: Path, text: str, was: str | None) -> None:
        target = path.resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        self._refuse_changed_meanwhile(target, was)
        writing = target.parent / f".{target.name}.{secrets.token_hex(8)}.writing"
        file = os.open(writing, NEW_FILE, self._mode_of(target))
        try:
            _fill(file, text)
            os.replace(writing, target)
        except BaseException:
            os.unlink(writing)
            raise

    def remove(self, path: Path) -> None:
        path.unlink(missing_ok=True)

    def _refuse_changed_meanwhile(self, target: Path, was: str | None) -> None:
        if was is not None and self.read(target) != was:
            raise ShortcutRefused(f"{target} changed while the shortcut was being written; nothing was saved, try again")

    def _mode_of(self, target: Path) -> int:
        if not target.exists():
            return NEW_FILE_MODE
        return target.stat().st_mode & 0o7777


def _fill(file: int, text: str) -> None:
    with os.fdopen(file, "w", encoding="utf-8") as opened:
        opened.write(text)
        opened.flush()
        os.fsync(opened.fileno())
