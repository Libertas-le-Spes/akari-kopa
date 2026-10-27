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

    def stored(self) -> dict:
        return {"kind": "web", "text": self.text, "forgeHost": self.forge_host}


@dataclass(frozen=True)
class RefusedAddress:
    reason: str
    forge_host: str
    text: str = ""

    def open_with(self, opener: Callable[[WebAddress], None]) -> None:
        return None

    def notes(self) -> list[str]:
        return [f"not opened: {self.reason}"]

    def stored(self) -> dict:
        return {"kind": "refused", "reason": self.reason, "forgeHost": self.forge_host}
