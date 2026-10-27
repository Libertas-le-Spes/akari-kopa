from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class WebAddress:
    text: str
    forge_host: str

    def open_with(self, opener: Callable[["WebAddress"], None]) -> None:
        opener(self)

    def notes(self) -> list[str]:
        return []


@dataclass(frozen=True)
class RefusedAddress:
    reason: str
    forge_host: str
    text: str = ""

    def open_with(self, opener: Callable[[WebAddress], None]) -> None:
        return None

    def notes(self) -> list[str]:
        return [f"not opened: {self.reason}"]
