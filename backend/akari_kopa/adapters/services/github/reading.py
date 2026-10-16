from akari_kopa.adapters.services.moment import latest, moment, moments
from akari_kopa.attention.conversation.conversation import Conversation
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import Role
from akari_kopa.attention.pipeline.pipeline import PipelineWords
from akari_kopa.attention.repository.follow_up import OWN, SOMEONE_ELSES

WORDS = PipelineWords(frozenset({"SUCCESS"}), frozenset({"FAILURE", "ERROR"}))
CAN_PUSH = {"ADMIN", "MAINTAIN", "WRITE"}


def merge_request(node: dict, role: Role) -> MergeRequest:
    commit = node["commits"]["nodes"][0]["commit"]
    author = node["author"] or {}
    return MergeRequest(
        service="github",
        role=role,
        reference=f"#{node['number']}",
        title=node["title"],
        url=node["url"],
        project=node["repository"]["nameWithOwner"],
        author=author.get("name") or author.get("login", ""),
        pipeline=WORDS.read([(commit["statusCheckRollup"] or {}).get("state")]),
        opened=moment(node["createdAt"]),
    )


def repository_of(node: dict):
    return OWN if node["repository"]["viewerPermission"] in CAN_PUSH else SOMEONE_ELSES


class ConversationReading:
    def __init__(self, me: str):
        self.me = me

    def conversation(self, node: dict, threads: list[dict]) -> Conversation:
        return Conversation(
            unresolved_threads=moments(first["createdAt"] for first in self._unresolved_openers(threads) if self._from_others(first)),
            comments=moments(self._others_comments(node)),
            last_answer=latest(self._my_answers(node)),
        )

    def _unresolved_openers(self, threads: list[dict]) -> list[dict]:
        return [thread["comments"]["nodes"][0] for thread in threads if not thread["isResolved"] and thread["comments"]["nodes"]]

    def _others_comments(self, node: dict):
        yield from (comment["createdAt"] for comment in node["comments"]["nodes"] if self._from_others(comment))
        yield from (review["submittedAt"] for review in node["reviews"]["nodes"] if self._from_others(review) and _says_something(review))

    def _my_answers(self, node: dict):
        yield from (comment["createdAt"] for comment in node["comments"]["nodes"] if self._from_me(comment))
        yield from (review["submittedAt"] for review in node["reviews"]["nodes"] if self._from_me(review))
        yield node["commits"]["nodes"][0]["commit"]["committedDate"]

    def _from_me(self, said: dict) -> bool:
        return (said["author"] or {}).get("login") == self.me

    def _from_others(self, said: dict) -> bool:
        return said["author"] is not None and self._another_person(said["author"])

    def _another_person(self, author: dict) -> bool:
        return author["login"] != self.me and author["__typename"] != "Bot"


def _says_something(review: dict) -> bool:
    return review["state"] != "APPROVED" and bool(review["body"])
