from akari_kopa.adapters.services.moment import latest, moments
from akari_kopa.attention.conversation.conversation import Conversation

OPEN_THREAD = {"active", "pending"}
NO_STATUS = {None, "unknown"}


class ConversationReading:
    def __init__(self, me: str):
        self.me = me

    def conversation(self, threads: list[dict], commits: list[dict]) -> Conversation:
        unresolved = []
        comments = []
        for thread in threads:
            if _written_by_a_person(thread) and self._opened_by_others(thread):
                _sort_by_status(thread, unresolved, comments)
        return Conversation(unresolved_threads=moments(unresolved), comments=moments(comments),
                            last_answer=latest(self._my_answers(threads, commits)))

    def _opened_by_others(self, thread: dict) -> bool:
        return thread["comments"][0]["author"]["id"] != self.me

    def _my_answers(self, threads: list[dict], commits: list[dict]) -> list[str]:
        found = []
        for thread in threads:
            for said in thread["comments"]:
                if said["author"]["id"] == self.me:
                    found.append(said["publishedDate"])
        for commit in commits:
            found.append(commit["committer"]["date"])
        return found


def _sort_by_status(thread: dict, unresolved: list[str], comments: list[str]) -> None:
    opened = thread["comments"][0]["publishedDate"]
    if thread.get("status") in OPEN_THREAD:
        unresolved.append(opened)
    if thread.get("status") in NO_STATUS:
        comments.append(opened)


def _written_by_a_person(thread: dict) -> bool:
    comments = thread["comments"]
    if thread.get("isDeleted") or not comments:
        return False
    return comments[0].get("commentType") == "text"
