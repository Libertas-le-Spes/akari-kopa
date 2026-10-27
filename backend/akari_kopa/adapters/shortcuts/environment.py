import os
from dataclasses import dataclass
from pathlib import Path

from akari_kopa.adapters.storage.xdg_folders import base_folder


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
        _desktops(os.environ.get("XDG_CURRENT_DESKTOP", "")),
        base_folder("XDG_CONFIG_HOME", home / ".config"),
        base_folder("XDG_DATA_HOME", home / ".local" / "share"),
    )


def _desktops(named: str) -> frozenset[str]:
    desktops = set()
    for name in named.split(":"):
        if name:
            desktops.add(name.lower())
    return frozenset(desktops)
