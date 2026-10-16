from urllib.parse import quote

from merge_requests.adapters.services.moment import latest, moment, moments
from merge_requests.attention.conversation.conversation import Conversation
from merge_requests.attention.merge_request.merge_request import MergeRequest
from merge_requests.attention.merge_request.role import Role
from merge_requests.attention.pipeline.pipeline import PipelineWords
from merge_requests.attention.repository.follow_up import OWN, SOMEONE_ELSES

WORDS = PipelineWords(frozenset({"succeeded", "partiallySucceeded"}), frozenset({"failed", "canceled"}))
OPEN_THREAD = {"active", "pending"}
NO_STATUS = {None, "unknown"}


def build_state(build: dict) -> str:
    return build.get("result") if build["status"] == "completed" else build["status"]


def merge_request(organisation: str, pull_request: dict, builds: list[dict], role: Role) -> MergeRequest:
    repository = pull_request["repository"]
    project = repository["project"]["name"]
    number = pull_request["pullRequestId"]
    return MergeRequest(
        service="azure-devops",
        role=role,
        reference=f"!{number}",
        title=pull_request["title"],
        url=f"https://dev.azure.com/{quote(organisation)}/{quote(project)}/_git/{quote(repository['name'])}/pullrequest/{number}",
        project=f"{project}/{repository['name']}",
        author=pull_request["createdBy"]["displayName"],
        pipeline=WORDS.read(build_state(build) for build in builds),
        opened=moment(pull_request["creationDate"]),
    )


def repository_of(evaluation: dict):
    return OWN if all(each["value"] for each in evaluation["evaluations"]) else SOMEONE_ELSES


class ConversationReading:
    def __init__(self, me: str):
        self.me = me

    def conversation(self, threads: list[dict], commits: list[dict]) -> Conversation:
        human = [thread for thread in threads if _written_by_a_person(thread)]
        return Conversation(
            unresolved_threads=moments(self._opened_by_others(thread) for thread in human if thread.get("status") in OPEN_THREAD),
            comments=moments(self._opened_by_others(thread) for thread in human if thread.get("status") in NO_STATUS),
            last_answer=latest([*self._my_comments(threads), *(commit["committer"]["date"] for commit in commits)]),
        )

    def _opened_by_others(self, thread: dict) -> str | None:
        opener = thread["comments"][0]
        return opener["publishedDate"] if opener["author"]["id"] != self.me else None

    def _my_comments(self, threads: list[dict]):
        return (said["publishedDate"] for thread in threads for said in thread["comments"] if said["author"]["id"] == self.me)


def _written_by_a_person(thread: dict) -> bool:
    return not thread.get("isDeleted") and _opened_with_text(thread["comments"])


def _opened_with_text(comments: list[dict]) -> bool:
    return bool(comments) and comments[0].get("commentType") == "text"
