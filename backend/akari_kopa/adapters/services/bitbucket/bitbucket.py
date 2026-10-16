from dataclasses import replace
from datetime import timedelta
from typing import Callable

from akari_kopa.adapters.keyring.secret_tool import SecretTool
from akari_kopa.adapters.services.bitbucket.reading import ConversationReading, merge_request, repository_of
from akari_kopa.adapters.transport.https import Https
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import MINE, REVIEWING
from akari_kopa.use_cases.listing.ports import Clock

API = "https://api.bitbucket.org/2.0"
KEYRING = ("akari-kopa", "bitbucket.org")
RECENTLY = timedelta(days=30)


class Bitbucket:
    name = "bitbucket"
    asked_every = timedelta(minutes=5)

    def __init__(self, keyring: SecretTool, connect: Callable[[str, str], Https], clock: Clock):
        self.keyring = keyring
        self.connect = connect
        self.clock = clock

    def is_set_up(self) -> bool:
        return bool(self.keyring.lookup(*KEYRING))

    def merge_requests(self) -> list[MergeRequest]:
        api = self.connect(API, self.keyring.lookup(*KEYRING))
        reading = ConversationReading(api.get("/user")["uuid"])
        workspaces = [each["workspace"]["slug"] for each in api.pages("/user/workspaces", pagelen="100")]
        return [found for workspace in workspaces for found in self._in(api, workspace, reading)]

    def _in(self, api: Https, workspace: str, reading: ConversationReading) -> list[MergeRequest]:
        mine = api.pages(f"/workspaces/{workspace}/pullrequests/{reading.me}", state="OPEN", pagelen="50")
        return [self._mine(api, pull_request, reading) for pull_request in mine] + self._reviewing(api, workspace, reading.me)

    def _reviewing(self, api: Https, workspace: str, me: str) -> list[MergeRequest]:
        since = (self.clock() - RECENTLY).strftime("%Y-%m-%dT%H:%M:%S")
        repositories = api.pages(f"/repositories/{workspace}", role="member", q=f"updated_on > {since}", sort="-updated_on", pagelen="100")
        asked = f'state="OPEN" AND reviewers.uuid="{me}"'
        pull_requests = [
            each for repository in repositories
            for each in api.pages(f"/repositories/{repository['full_name']}/pullrequests", q=asked, pagelen="50")
        ]
        return [merge_request(each, self._statuses(api, each), REVIEWING) for each in pull_requests]

    def _mine(self, api: Https, pull_request: dict, reading: ConversationReading) -> MergeRequest:
        path = _path(pull_request)
        comments = api.pages(f"{path}/comments", pagelen="100")
        commits = api.get(f"{path}/commits", pagelen="1")["values"]
        permissions = api.pages("/user/permissions/repositories", q=f'repository.full_name="{_repository(pull_request)}"')
        found = merge_request(pull_request, self._statuses(api, pull_request), MINE)
        return replace(found, conversation=reading.conversation(comments, commits), repository=repository_of(permissions))

    def _statuses(self, api: Https, pull_request: dict) -> list[dict]:
        return api.pages(f"{_path(pull_request)}/statuses", pagelen="100")


def _repository(pull_request: dict) -> str:
    return pull_request["destination"]["repository"]["full_name"]


def _path(pull_request: dict) -> str:
    return f"/repositories/{_repository(pull_request)}/pullrequests/{pull_request['id']}"
