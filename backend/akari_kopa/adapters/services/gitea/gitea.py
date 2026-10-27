from dataclasses import replace
from datetime import timedelta

from akari_kopa.adapters.services.gitea.conversation_parts import ConversationParts
from akari_kopa.adapters.services.gitea.reading import ConversationReading, merge_request, repository_of
from akari_kopa.adapters.services.gitea.tea import Tea, TeaLogin
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import MINE, REVIEWING


class Gitea:
    name = "gitea"
    heading = "Gitea / Forgejo"
    asked_every = timedelta(0)

    def __init__(self, tea: Tea):
        self.tea = tea
        self.parts = ConversationParts(tea)

    def is_set_up(self) -> bool:
        return self.tea.installed()

    def merge_requests(self) -> list[MergeRequest]:
        found = []
        for login in self.tea.logins():
            found += self._on(login)
        return found

    def _on(self, login: TeaLogin) -> list[MergeRequest]:
        reading = ConversationReading(self.tea.get(login, "/user")["login"])
        found = []
        for issue in self._search(login, "created"):
            found.append(self._mine(login, issue, reading))
        for issue in self._search(login, "review_requested"):
            found.append(self._reviewing(login, issue))
        return found

    def _search(self, login: TeaLogin, search: str) -> list[dict]:
        return self.tea.get(login, f"/repos/issues/search?type=pulls&state=open&{search}=true&limit=50")

    def _reviewing(self, login: TeaLogin, issue: dict) -> MergeRequest:
        pull, status = self.parts.pull_and_status(login, issue)
        return merge_request(issue, pull, status, login.host, REVIEWING)

    def _mine(self, login: TeaLogin, issue: dict, reading: ConversationReading) -> MergeRequest:
        pull, status = self.parts.pull_and_status(login, issue)
        comments, reviews, review_comments, head_commit = self.parts.of(login, issue, pull)
        conversation = reading.conversation(comments, reviews, review_comments, head_commit)
        return replace(merge_request(issue, pull, status, login.host, MINE), conversation=conversation, repository=repository_of(pull))
