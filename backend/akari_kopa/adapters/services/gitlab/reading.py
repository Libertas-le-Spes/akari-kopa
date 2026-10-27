from akari_kopa.adapters.services.moment import latest, moment, moments
from akari_kopa.attention.conversation.conversation import Conversation
from akari_kopa.attention.merge_request.address_check import address_of
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import Role
from akari_kopa.attention.pipeline.pipeline import PipelineWords
from akari_kopa.attention.repository.follow_up import OWN, SOMEONE_ELSES

WORDS = PipelineWords(frozenset({"SUCCESS", "MANUAL", "SKIPPED"}), frozenset({"FAILED", "CANCELED"}))


def merge_request(node: dict, host: str, role: Role) -> MergeRequest:
    return MergeRequest(
        service="gitlab",
        role=role,
        reference=f"!{node['iid']}",
        title=node["title"],
        address=address_of(node["webUrl"], host),
        project=node["project"]["fullPath"],
        author=_author(node["author"]),
        pipeline=WORDS.read([_pipeline_status(node["headPipeline"])]),
        opened=moment(node["createdAt"]),
    )


def _author(author: dict) -> str:
    if author["name"]:
        return author["name"]
    return author["username"]


def _pipeline_status(pipeline: dict | None) -> str | None:
    if pipeline is None:
        return None
    return pipeline.get("status")


def repository_of(node: dict):
    if node["project"]["userPermissions"]["pushCode"]:
        return OWN
    return SOMEONE_ELSES


class ConversationReading:
    def __init__(self, me: str):
        self.me = me

    def conversation(self, discussions: list[dict]) -> Conversation:
        openers = _openers(discussions)
        unresolved = []
        comments = []
        mine = []
        for note in openers:
            if _unresolved(note) and self._from_others(note):
                unresolved.append(note["createdAt"])
            if _plain_comment(note) and self._from_others(note):
                comments.append(note["createdAt"])
            if note["author"]["username"] == self.me:
                mine.append(note["createdAt"])
        return Conversation(unresolved_threads=moments(unresolved), comments=moments(comments), last_answer=latest(mine))

    def _from_others(self, note: dict) -> bool:
        return note["author"]["username"] != self.me and not note["author"]["bot"]


def _openers(discussions: list[dict]) -> list[dict]:
    openers = []
    for discussion in discussions:
        if discussion["notes"]["nodes"]:
            openers.append(_opener(discussion))
    return openers


def _opener(discussion: dict) -> dict:
    opener = dict(discussion["notes"]["nodes"][0])
    opener["resolvable"] = discussion["resolvable"]
    opener["resolved"] = discussion["resolved"]
    return opener


def _unresolved(note: dict) -> bool:
    return note["resolvable"] and not note["resolved"]


def _plain_comment(note: dict) -> bool:
    return not note["resolvable"] and not note["system"]
