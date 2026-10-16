from dataclasses import replace
from datetime import timedelta

from merge_requests.adapters.services.gitea.reading import ConversationReading, merge_request, repository_of
from merge_requests.adapters.services.gitea.tea import Tea
from merge_requests.attention.merge_request.merge_request import MergeRequest
from merge_requests.attention.merge_request.role import MINE, REVIEWING

class Gitea:
    name = "gitea"
    asked_every = timedelta(0)

    def __init__(self, tea: Tea):
        self.tea = tea

    def is_set_up(self) -> bool:
        return self.tea.installed()

    def merge_requests(self) -> list[MergeRequest]:
        return [found for login in self.tea.logins() for found in self._on(login)]

    def _on(self, login: str) -> list[MergeRequest]:
        reading = ConversationReading(self.tea.get(login, "/user")["login"])
        mine = [self._mine(login, issue, reading) for issue in self._search(login, "created")]
        reviewing = [self._reviewing(login, issue) for issue in self._search(login, "review_requested")]
        return mine + reviewing

    def _search(self, login: str, search: str) -> list[dict]:
        return self.tea.get(login, f"/repos/issues/search?type=pulls&state=open&{search}=true&limit=50")

    def _reviewing(self, login: str, issue: dict) -> MergeRequest:
        pull, status = self._pull_and_status(login, issue)
        return merge_request(issue, pull, status, REVIEWING)

    def _mine(self, login: str, issue: dict, reading: ConversationReading) -> MergeRequest:
        pull, status = self._pull_and_status(login, issue)
        conversation = reading.conversation(*self._conversation_parts(login, issue, pull))
        return replace(merge_request(issue, pull, status, MINE), conversation=conversation, repository=repository_of(pull))

    def _pull_and_status(self, login: str, issue: dict) -> tuple[dict, dict]:
        repo = issue["repository"]["full_name"]
        pull = self.tea.get(login, f"/repos/{repo}/pulls/{issue['number']}")
        return pull, self.tea.get(login, f"/repos/{repo}/commits/{pull['head']['sha']}/status")

    def _conversation_parts(self, login: str, issue: dict, pull: dict) -> tuple[list[dict], list[dict], list[dict], dict]:
        repo, number = issue["repository"]["full_name"], issue["number"]
        reviews = self.tea.get(login, f"/repos/{repo}/pulls/{number}/reviews")
        review_comments = [
            said for review in reviews
            for said in self.tea.get(login, f"/repos/{repo}/pulls/{number}/reviews/{review['id']}/comments")
        ]
        comments = self.tea.get(login, f"/repos/{repo}/issues/{number}/comments")
        head_commit = self.tea.get(login, f"/repos/{repo}/git/commits/{pull['head']['sha']}")
        return comments, reviews, review_comments, head_commit
