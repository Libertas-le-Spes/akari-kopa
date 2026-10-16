from akari_kopa.adapters.services.moment import latest, moment, moments
from akari_kopa.attention.conversation.conversation import Conversation
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import Role
from akari_kopa.attention.pipeline.pipeline import PipelineWords
from akari_kopa.attention.repository.follow_up import OWN, SOMEONE_ELSES

WORDS = PipelineWords(frozenset({"SUCCESSFUL"}), frozenset({"FAILED", "STOPPED"}))
CAN_PUSH = {"write", "admin"}


def merge_request(pull_request: dict, statuses: list[dict], role: Role) -> MergeRequest:
    return MergeRequest(
        service="bitbucket",
        role=role,
        reference=f"#{pull_request['id']}",
        title=pull_request["title"],
        url=pull_request["links"]["html"]["href"],
        project=pull_request["destination"]["repository"]["full_name"],
        author=pull_request["author"]["display_name"],
        pipeline=WORDS.read(status["state"] for status in statuses),
        opened=moment(pull_request["created_on"]),
    )


def repository_of(permissions: list[dict]):
    return OWN if any(permission["permission"] in CAN_PUSH for permission in permissions) else SOMEONE_ELSES


class ConversationReading:
    def __init__(self, me: str):
        self.me = me

    def conversation(self, comments: list[dict], commits: list[dict]) -> Conversation:
        openers = [said for said in comments if "parent" not in said and not said.get("deleted")]
        return Conversation(
            unresolved_threads=moments(said["created_on"] for said in openers if _unresolved_inline(said) and self._from_others(said)),
            comments=moments(said["created_on"] for said in openers if "inline" not in said and self._from_others(said)),
            last_answer=latest([*(said["created_on"] for said in comments if self._from_me(said)), *(commit["date"] for commit in commits)]),
        )

    def _from_me(self, said: dict) -> bool:
        return (said.get("user") or {}).get("uuid") == self.me

    def _from_others(self, said: dict) -> bool:
        user = said.get("user")
        return user is not None and user.get("uuid") != self.me


def _unresolved_inline(said: dict) -> bool:
    return "inline" in said and said.get("resolution") is None
