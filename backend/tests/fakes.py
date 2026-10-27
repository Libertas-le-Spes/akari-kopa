from dataclasses import replace
from datetime import datetime, timedelta, timezone

from akari_kopa.adapters.storage.answer_folder import StoredAnswer
from akari_kopa.attention.conversation.conversation import Conversation
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import MINE
from akari_kopa.attention.merge_request.web_address import WebAddress
from akari_kopa.attention.pipeline.pipeline import NO_PIPELINE
from akari_kopa.use_cases.listing.ports import ServiceError

OPENED = datetime(2026, 10, 1, tzinfo=timezone.utc)
FORGE_PAGE = WebAddress("https://forge.example/1", "forge.example")


def on_day(day: float) -> datetime:
    return OPENED + timedelta(days=day)


def a_merge_request(**changes) -> MergeRequest:
    plain = MergeRequest("forge", MINE, "#1", "Fix the thing", FORGE_PAGE, "me/thing", "Me", NO_PIPELINE, OPENED)
    return replace(plain, **changes)


def commented_on(day: float) -> Conversation:
    return Conversation(comments=(on_day(day),))


class Clock:
    def __init__(self, now: datetime = OPENED):
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class FakeService:
    def __init__(self, name: str, *merge_requests: MergeRequest, asked_every: timedelta = timedelta(0)):
        self.name = name
        self.heading = name.title()
        self.asked_every = asked_every
        self.answer = list(merge_requests)
        self.failure: Exception | None = None
        self.times_asked = 0
        self.set_up = True

    def is_set_up(self) -> bool:
        return self.set_up

    def merge_requests(self) -> list[MergeRequest]:
        self.times_asked += 1
        if self.failure:
            raise self.failure
        return self.answer

    def fails(self, reason: str) -> None:
        self.failure = ServiceError(reason)


class FakeAnswers:
    def __init__(self):
        self.kept = {}

    def last(self, service):
        return self.kept.get(service)

    def keep(self, service, merge_requests, given):
        self.kept[service] = StoredAnswer(merge_requests, given)
