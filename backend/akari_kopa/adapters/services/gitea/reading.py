from akari_kopa.adapters.services.moment import latest, moment, moments
from akari_kopa.attention.conversation.conversation import Conversation
from akari_kopa.attention.merge_request.address_check import address_of
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import Role
from akari_kopa.attention.pipeline.pipeline import NO_PIPELINE, Pipeline, PipelineWords
from akari_kopa.attention.repository.follow_up import OWN, SOMEONE_ELSES

WORDS = PipelineWords(frozenset({"success"}), frozenset({"failure", "error"}))


def pipeline_of(status: dict) -> Pipeline:
    if not status["total_count"]:
        return NO_PIPELINE
    return WORDS.read([status["state"]])


def merge_request(issue: dict, pull: dict, status: dict, host: str, role: Role) -> MergeRequest:
    return MergeRequest(
        service="gitea",
        role=role,
        reference=f"#{issue['number']}",
        title=issue["title"],
        address=address_of(issue["html_url"], host),
        project=issue["repository"]["full_name"],
        author=_author(issue["user"]),
        pipeline=pipeline_of(status),
        opened=moment(pull["created_at"]),
    )


def _author(user: dict) -> str:
    if user.get("full_name"):
        return user["full_name"]
    return user["login"]


def repository_of(pull: dict):
    if pull["base"]["repo"]["permissions"]["push"]:
        return OWN
    return SOMEONE_ELSES


class ConversationReading:
    def __init__(self, me: str):
        self.me = me

    def conversation(self, comments: list[dict], reviews: list[dict], review_comments: list[dict], head_commit: dict) -> Conversation:
        return Conversation(
            unresolved_threads=moments(self._unresolved(review_comments)),
            comments=moments(self._others_comments(comments, reviews)),
            last_answer=latest(self._my_answers(comments, reviews, head_commit)),
        )

    def _unresolved(self, review_comments: list[dict]) -> list[str]:
        found = []
        for said in review_comments:
            if said["resolver"] is None and self._from_others(said):
                found.append(said["created_at"])
        return found

    def _others_comments(self, comments: list[dict], reviews: list[dict]) -> list[str]:
        found = []
        for said in comments:
            if self._from_others(said):
                found.append(said["created_at"])
        for review in reviews:
            if self._from_others(review) and _says_something(review):
                found.append(review["submitted_at"])
        return found

    def _my_answers(self, comments: list[dict], reviews: list[dict], head_commit: dict) -> list[str]:
        found = []
        for said in comments:
            if self._from_me(said):
                found.append(said["created_at"])
        for review in reviews:
            if self._from_me(review):
                found.append(review["submitted_at"])
        found.append(head_commit["commit"]["committer"]["date"])
        return found

    def _from_me(self, said: dict) -> bool:
        user = said.get("user")
        return user is not None and user.get("login") == self.me

    def _from_others(self, said: dict) -> bool:
        user = said.get("user")
        return user is not None and user["login"] != self.me


def _says_something(review: dict) -> bool:
    return review["state"] != "APPROVED" and bool(review["body"])
