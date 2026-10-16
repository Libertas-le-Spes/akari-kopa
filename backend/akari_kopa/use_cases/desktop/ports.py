from dataclasses import dataclass
from typing import Callable, Protocol


@dataclass(frozen=True)
class MenuEntry:
    label: str | None
    action: Callable[[], None] | None = None


SEPARATOR = MenuEntry(None)


@dataclass(frozen=True)
class Pixmap:
    width: int
    height: int
    argb: bytes


@dataclass(frozen=True)
class IconContent:
    title: str
    description: str
    pixmaps: list[Pixmap]
    menu: list[MenuEntry]
    on_activate: Callable[[], None] | None = None


class Icon(Protocol):
    def register(self) -> None: ...
    def update(self, content: IconContent) -> None: ...
    def close(self) -> None: ...


class Desktop(Protocol):
    def show_icon(self, key: str, content: IconContent) -> Icon: ...
    def notify(self, summary: str, body: str) -> None: ...
    def open_in_browser(self, url: str) -> None: ...
    def when_tray_returns(self, then: Callable[[], None]) -> None: ...
    def every(self, seconds: int, then: Callable[[], None]) -> None: ...
    def in_background(self, work: Callable[[], object], then: Callable[[object], None]) -> None: ...
    def run_until_stopped(self) -> None: ...
