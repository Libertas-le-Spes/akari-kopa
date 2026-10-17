from dataclasses import replace
from datetime import timedelta
from typing import Callable
from urllib.parse import quote

from akari_kopa.adapters.services.azure_devops.az import Az
from akari_kopa.adapters.services.azure_devops.reading import ConversationReading, merge_request, repository_of
from akari_kopa.adapters.transport.https import Https
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import MINE, REVIEWING

PROFILES = "https://app.vssps.visualstudio.com/_apis"
ORGANISATIONS = "https://dev.azure.com"
VERSION = "7.1"
GIT_REPOSITORIES_SECURITY = "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
CONTRIBUTE = 4


class AzureDevOps:
    name = "azure-devops"
    heading = "Azure DevOps"
    asked_every = timedelta(0)

    def __init__(self, az: Az, connect: Callable[[str, str], Https]):
        self.az = az
        self.connect = connect

    def is_set_up(self) -> bool:
        return self.az.installed()

    def merge_requests(self) -> list[MergeRequest]:
        token = self.az.access_token()
        if not token:
            return []
        api = self.connect("", token)
        me = api.get(f"{PROFILES}/profile/profiles/me", **{"api-version": VERSION})["id"]
        organisations = api.get(f"{PROFILES}/accounts", memberId=me, **{"api-version": VERSION})["value"]
        reading = ConversationReading(me)
        return [found for organisation in organisations for found in self._in(api, organisation["accountName"], reading)]

    def _in(self, api: Https, organisation: str, reading: ConversationReading) -> list[MergeRequest]:
        mine = [self._mine(api, organisation, each, reading) for each in self._pull_requests(api, organisation, "creatorId", reading.me)]
        reviewing = [self._reviewing(api, organisation, each) for each in self._pull_requests(api, organisation, "reviewerId", reading.me)]
        return mine + reviewing

    def _pull_requests(self, api: Https, organisation: str, criterion: str, me: str) -> list[dict]:
        found = api.get(
            f"{ORGANISATIONS}/{quote(organisation)}/_apis/git/pullrequests",
            **{f"searchCriteria.{criterion}": me, "searchCriteria.status": "active", "$top": "100", "api-version": VERSION},
        )
        return found["value"]

    def _reviewing(self, api: Https, organisation: str, pull_request: dict) -> MergeRequest:
        return merge_request(organisation, pull_request, self._builds(api, organisation, pull_request), REVIEWING)

    def _mine(self, api: Https, organisation: str, pull_request: dict, reading: ConversationReading) -> MergeRequest:
        found = merge_request(organisation, pull_request, self._builds(api, organisation, pull_request), MINE)
        threads = api.get(f"{_pull_request_path(organisation, pull_request)}/threads", **{"api-version": VERSION})["value"]
        commits = api.get(f"{_pull_request_path(organisation, pull_request)}/commits", **{"$top": "1", "api-version": VERSION})["value"]
        evaluation = api.post(f"{ORGANISATIONS}/{quote(organisation)}/_apis/security/permissionevaluationbatch",
                              _may_contribute(pull_request), **{"api-version": VERSION})
        return replace(found, conversation=reading.conversation(threads, commits), repository=repository_of(evaluation))

    def _builds(self, api: Https, organisation: str, pull_request: dict) -> list[dict]:
        project = pull_request["repository"]["project"]["id"]
        found = api.get(
            f"{ORGANISATIONS}/{quote(organisation)}/{project}/_apis/build/builds",
            branchName=f"refs/pull/{pull_request['pullRequestId']}/merge",
            maxBuildsPerDefinition="1", queryOrder="queueTimeDescending", **{"api-version": VERSION},
        )
        return found["value"]


def _pull_request_path(organisation: str, pull_request: dict) -> str:
    repository = pull_request["repository"]
    return (f"{ORGANISATIONS}/{quote(organisation)}/{repository['project']['id']}/_apis/git/repositories/{repository['id']}"
            f"/pullRequests/{pull_request['pullRequestId']}")


def _may_contribute(pull_request: dict) -> dict:
    repository = pull_request["repository"]
    token = f"repoV2/{repository['project']['id']}/{repository['id']}"
    return {"alwaysAllowAdministrators": False,
            "evaluations": [{"securityNamespaceId": GIT_REPOSITORIES_SECURITY, "token": token, "permissions": CONTRIBUTE}]}
