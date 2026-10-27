from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent.parent
PACKAGE = REPOSITORY / "backend" / "akari_kopa"


def relative(path: Path) -> str:
    return str(path.relative_to(REPOSITORY))


def files_saying(text: str, folder: Path, pattern: str) -> list[str]:
    found = []
    for path in sorted(folder.rglob(pattern)):
        if text in path.read_text(encoding="utf-8"):
            found.append(relative(path))
    return found


def read(relative_path: str) -> str:
    return (REPOSITORY / relative_path).read_text(encoding="utf-8")
