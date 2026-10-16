import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Environment:
    desktops: frozenset[str]
    config_home: Path
    data_home: Path

    def is_one_of(self, names: set[str]) -> bool:
        return bool(self.desktops & names)


def this_session() -> Environment:
    home = Path.home()
    return Environment(
        frozenset(name.lower() for name in os.environ.get("XDG_CURRENT_DESKTOP", "").split(":") if name),
        Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config"),
        Path(os.environ.get("XDG_DATA_HOME") or home / ".local" / "share"),
    )
