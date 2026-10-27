from akari_kopa.adapters.services.github.people import People
from akari_kopa.adapters.services.moment import latest, moment, moments
from akari_kopa.attention.conversation.conversation import Conversation
from akari_kopa.attention.merge_request.address_check import address_of
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import Role
from akari_kopa.attention.pipeline.pipeline import PipelineWords
from akari_kopa.attention.repository.follow_up import OWN, SOMEONE_ELSES

WORDS = PipelineWords(frozenset({"SUCCESS"}), frozenset({"FAILURE", "ERROR"}))
CAN_PUSH = {"ADMIN", "MAINTAIN", "WRITE"}


def merge_request(node: dict, host: str, role: Role) -> MergeRequest:
    commit = node["commits"]["nodes"][0]["commit"]
    return MergeRequest(
        service="github",
        role=role,
        reference=f"#{node['number']}",
        title=node["title"],
        address=address_of(node["url"], host),
        project=node["repository"]["nameWithOwner"],
        author=_author(node["author"]),
        pipeline=WORDS.read([_checks_state(commit["statusCheckRollup"])]),
        opened=moment(node["createdAt"]),
    )


def _author(author: dict | None) -> str:
    if author is None:
        return ""
    if author.get("name"):
        return author["name"]
    return author.get("login", "")


def _checks_state(rollup: dict | None) -> str | None:
    if rollup is None:
        return None
    return rollup.get("state")


def repository_of(node: dict):
    if node["repository"]["viewerPermission"] in CAN_PUSH:
        return OWN
    return SOMEONE_ELSES


class ConversationReading:
    def __init__(self, me: str):
        self.people = People(me)

    def conversation(self, node: dict, threads: list[dict]) -> Conversation:
        return Conversation(
            unresolved_threads=moments(self._waiting_threads(threads)),
            comments=moments(self._others_comments(node)),
            last_answer=latest(self._my_answers(node)),
        )

    def _waiting_threads(self, threads: list[dict]) -> list[str]:
        waiting = []
        for thread in threads:
            if self._waits(thread):
                waiting.append(thread["comments"]["nodes"][0]["createdAt"])
        return waiting

    def _waits(self, thread: dict) -> bool:
        openers = thread["comments"]["nodes"]
        if thread["isResolved"] or not openers:
            return False
        return self.people.from_others(openers[0])

    def _others_comments(self, node: dict) -> list[str]:
        found = []
        for comment in node["comments"]["nodes"]:
            if self.people.from_others(comment):
                found.append(comment["createdAt"])
        for review in node["reviews"]["nodes"]:
            if self.people.from_others(review) and _says_something(review):
                found.append(review["submittedAt"])
        return found

    def _my_answers(self, node: dict) -> list[str]:
        found = []
        for comment in node["comments"]["nodes"]:
            if self.people.from_me(comment):
                found.append(comment["createdAt"])
        for review in node["reviews"]["nodes"]:
            if self.people.from_me(review):
                found.append(review["submittedAt"])
        found.append(node["commits"]["nodes"][0]["commit"]["committedDate"])
        return found


def _says_something(review: dict) -> bool:
    return review["state"] != "APPROVED" and bool(review["body"])
