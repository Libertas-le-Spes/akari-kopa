from dataclasses import replace
from datetime import datetime, timedelta, timezone

from merge_requests.adapters.storage.answer_folder import StoredAnswer
from merge_requests.attention.conversation.conversation import Conversation
from merge_requests.attention.merge_request.merge_request import MergeRequest
from merge_requests.attention.merge_request.role import MINE
from merge_requests.attention.pipeline.pipeline import NO_PIPELINE
from merge_requests.use_cases.listing.ports import ServiceError

OPENED = datetime(2026, 10, 1, tzinfo=timezone.utc)


def on_day(day: float) -> datetime:
    return OPENED + timedelta(days=day)


def a_merge_request(**changes) -> MergeRequest:
    plain = MergeRequest("forge", MINE, "#1", "Fix the thing", "https://forge.example/1", "me/thing", "Me", NO_PIPELINE, OPENED)
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


class FakeCommandLine:
    def __init__(self, tools: set[str], answers: dict[tuple, object] | None = None, said: dict[tuple, str] | None = None):
        self.tools = tools
        self.answers = answers or {}
        self.said = said or {}
        self.asked: list[tuple] = []

    def installed(self, tool: str) -> bool:
        return tool in self.tools

    def succeeds(self, *arguments: str) -> bool:
        return arguments in self.said or arguments[:2] == ("tea", "api")

    def everything_said(self, *arguments: str) -> str:
        return self.said.get(arguments, "")

    def json(self, *arguments: str):
        self.asked.append(arguments)
        for key, answer in self.answers.items():
            if all(part in arguments for part in key):
                return answer
        raise ServiceError(f"nothing prepared for {arguments}")
