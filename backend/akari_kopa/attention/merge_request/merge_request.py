from dataclasses import dataclass
from datetime import datetime

from akari_kopa.attention.conversation.conversation import QUIET, Conversation
from akari_kopa.attention.merge_request.role import Role
from akari_kopa.attention.pipeline.pipeline import Pipeline
from akari_kopa.attention.repository.follow_up import OWN
from akari_kopa.attention.repository.repository import Repository

COMMENTS = "comments"


@dataclass(frozen=True)
class MergeRequest:
    service: str
    role: Role
    reference: str
    title: str
    url: str
    project: str
    author: str
    pipeline: Pipeline
    opened: datetime
    conversation: Conversation = QUIET
    repository: Repository = OWN

    def waiting_on_me(self) -> bool:
        return self.conversation.waiting_since() is not None

    def standing(self) -> str:
        if self.waiting_on_me() and not self.pipeline.outranks_comments:
            return COMMENTS
        return self.pipeline.name

    def on_the_bar(self, now: datetime) -> bool:
        return self.repository.keeps_on_the_bar(self.opened, self.conversation, now)
