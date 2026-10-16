from datetime import datetime, timedelta
from typing import Callable, Protocol

from merge_requests.attention.merge_request.merge_request import MergeRequest

Clock = Callable[[], datetime]


class ServiceError(Exception):
    @property
    def reason(self) -> str:
        return str(self)


def reason_for(error: Exception) -> str:
    return getattr(error, "reason", f"unexpected answer: {type(error).__name__} {error}")


class Service(Protocol):
    name: str
    asked_every: timedelta

    def is_set_up(self) -> bool: ...
    def merge_requests(self) -> list[MergeRequest]: ...


class Answer(Protocol):
    merge_requests: list[MergeRequest]
    given: datetime


class Answers(Protocol):
    def last(self, service: str) -> Answer | None: ...
    def keep(self, service: str, merge_requests: list[MergeRequest], given: datetime) -> None: ...
