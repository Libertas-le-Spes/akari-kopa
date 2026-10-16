from akari_kopa.adapters.services.moment import latest, moment, moments
from akari_kopa.attention.conversation.conversation import Conversation
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import Role
from akari_kopa.attention.pipeline.pipeline import NO_PIPELINE, Pipeline, PipelineWords
from akari_kopa.attention.repository.follow_up import OWN, SOMEONE_ELSES

WORDS = PipelineWords(frozenset({"success"}), frozenset({"failure", "error"}))


def pipeline_of(status: dict) -> Pipeline:
    return WORDS.read([status["state"]]) if status["total_count"] else NO_PIPELINE


def merge_request(issue: dict, pull: dict, status: dict, role: Role) -> MergeRequest:
    return MergeRequest(
        service="gitea",
        role=role,
        reference=f"#{issue['number']}",
        title=issue["title"],
        url=issue["html_url"],
        project=issue["repository"]["full_name"],
        author=issue["user"].get("full_name") or issue["user"]["login"],
        pipeline=pipeline_of(status),
        opened=moment(pull["created_at"]),
    )


def repository_of(pull: dict):
    return OWN if pull["base"]["repo"]["permissions"]["push"] else SOMEONE_ELSES


class ConversationReading:
    def __init__(self, me: str):
        self.me = me

    def conversation(self, comments: list[dict], reviews: list[dict], review_comments: list[dict], head_commit: dict) -> Conversation:
        return Conversation(
            unresolved_threads=moments(said["created_at"] for said in review_comments if said["resolver"] is None and self._from_others(said)),
            comments=moments(self._others_comments(comments, reviews)),
            last_answer=latest([*(said["created_at"] for said in comments if self._from_me(said)),
                                *(review["submitted_at"] for review in reviews if self._from_me(review)),
                                head_commit["commit"]["committer"]["date"]]),
        )

    def _others_comments(self, comments: list[dict], reviews: list[dict]):
        yield from (said["created_at"] for said in comments if self._from_others(said))
        yield from (review["submitted_at"] for review in reviews if self._from_others(review) and _says_something(review))

    def _from_me(self, said: dict) -> bool:
        return (said.get("user") or {}).get("login") == self.me

    def _from_others(self, said: dict) -> bool:
        user = said.get("user")
        return user is not None and user["login"] != self.me


def _says_something(review: dict) -> bool:
    return review["state"] != "APPROVED" and bool(review["body"])
