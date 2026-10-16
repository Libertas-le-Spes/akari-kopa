from merge_requests.adapters.services.moment import latest, moment, moments
from merge_requests.attention.conversation.conversation import Conversation
from merge_requests.attention.merge_request.merge_request import MergeRequest
from merge_requests.attention.merge_request.role import Role
from merge_requests.attention.pipeline.pipeline import PipelineWords
from merge_requests.attention.repository.follow_up import OWN, SOMEONE_ELSES

WORDS = PipelineWords(frozenset({"SUCCESS", "MANUAL", "SKIPPED"}), frozenset({"FAILED", "CANCELED"}))


def merge_request(node: dict, role: Role) -> MergeRequest:
    return MergeRequest(
        service="gitlab",
        role=role,
        reference=f"!{node['iid']}",
        title=node["title"],
        url=node["webUrl"],
        project=node["project"]["fullPath"],
        author=node["author"]["name"] or node["author"]["username"],
        pipeline=WORDS.read([(node["headPipeline"] or {}).get("status")]),
        opened=moment(node["createdAt"]),
    )


def repository_of(node: dict):
    return OWN if node["project"]["userPermissions"]["pushCode"] else SOMEONE_ELSES


class ConversationReading:
    def __init__(self, me: str):
        self.me = me

    def conversation(self, discussions: list[dict]) -> Conversation:
        openers = [_opener(discussion) for discussion in discussions if discussion["notes"]["nodes"]]
        return Conversation(
            unresolved_threads=moments(note["createdAt"] for note in openers if _unresolved(note) and self._from_others(note)),
            comments=moments(note["createdAt"] for note in openers if _plain_comment(note) and self._from_others(note)),
            last_answer=latest(note["createdAt"] for note in openers if note["author"]["username"] == self.me),
        )

    def _from_others(self, note: dict) -> bool:
        return note["author"]["username"] != self.me and not note["author"]["bot"]


def _opener(discussion: dict) -> dict:
    return {"resolvable": discussion["resolvable"], "resolved": discussion["resolved"], **discussion["notes"]["nodes"][0]}


def _unresolved(note: dict) -> bool:
    return note["resolvable"] and not note["resolved"]


def _plain_comment(note: dict) -> bool:
    return not note["resolvable"] and not note["system"]
