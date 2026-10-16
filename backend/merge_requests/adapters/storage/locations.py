import os
from pathlib import Path


def answer_folder() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "kayu.merge-requests" / "answers"
