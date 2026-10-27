from pathlib import Path

from akari_kopa.adapters.storage.xdg_folders import base_folder


def answer_folder() -> str:
    return str(base_folder("XDG_CACHE_HOME", Path.home() / ".cache") / "kayu.akari-kopa" / "answers")
