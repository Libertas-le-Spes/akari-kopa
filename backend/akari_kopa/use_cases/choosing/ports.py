from dataclasses import dataclass
from typing import Protocol

from akari_kopa.attention.merge_request.web_address import WebAddress


@dataclass(frozen=True)
class Option:
    key: str
    label: str
    detail: str


class Chooser(Protocol):
    name: str

    def installed(self) -> bool: ...
    def choose(self, title: str, question: str, options: list[Option]) -> str | None: ...


class Browser(Protocol):
    def open(self, address: WebAddress) -> None: ...
