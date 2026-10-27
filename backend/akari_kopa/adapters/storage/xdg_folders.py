import os
from pathlib import Path


def base_folder(variable: str, usual: Path) -> Path:
    given = os.environ.get(variable, "")
    if given and Path(given).is_absolute():
        return Path(given)
    return usual
