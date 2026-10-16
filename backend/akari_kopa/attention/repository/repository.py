from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from akari_kopa.attention.conversation.conversation import Conversation


class Repository(Protocol):
    name: str

    def keeps_on_the_bar(self, opened: datetime, conversation: Conversation, now: datetime) -> bool: ...


class OwnRepository:
    name = "own"

    def keeps_on_the_bar(self, opened: datetime, conversation: Conversation, now: datetime) -> bool:
        return True


@dataclass(frozen=True)
class SomeoneElsesRepository:
    hold: timedelta
    checks: tuple[timedelta, ...]
    let_go: timedelta
    name: str = "someone else's"

    def keeps_on_the_bar(self, opened: datetime, conversation: Conversation, now: datetime) -> bool:
        age = now - opened
        if age >= self.let_go:
            return False
        return age < self.hold or self._seen_at_last_check(opened, conversation, age)

    def _seen_at_last_check(self, opened: datetime, conversation: Conversation, age: timedelta) -> bool:
        waiting_since = conversation.waiting_since()
        if waiting_since is None:
            return False
        last_check = max((check for check in self.checks if check <= age), default=None)
        return last_check is not None and waiting_since <= opened + last_check
