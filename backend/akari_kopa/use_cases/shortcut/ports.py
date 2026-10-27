from typing import Protocol

KEYS = "Super + Ctrl + M"


class ShortcutRefused(Exception):
    pass


class ShortcutHome(Protocol):
    name: str

    def here(self) -> bool: ...
    def has_it(self) -> bool: ...
    def add(self) -> None: ...
    def remove(self) -> None: ...
