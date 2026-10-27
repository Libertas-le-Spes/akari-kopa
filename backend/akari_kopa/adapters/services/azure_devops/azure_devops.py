from dataclasses import replace
from datetime import timedelta
from typing import Callable

from akari_kopa.adapters.services.azure_devops.az import Az
from akari_kopa.adapters.services.azure_devops.places import PROFILES, organisation_api, project_api, pull_request_api
from akari_kopa.adapters.services.azure_devops.conversation_reading import ConversationReading
from akari_kopa.adapters.services.azure_devops.reading import merge_request, repository_of
from akari_kopa.adapters.transport.https import Https
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import MINE, REVIEWING

VERSION = "7.1"
GIT_REPOSITORIES_SECURITY = "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
CONTRIBUTE = 4


class AzureDevOps:
    name = "azure-devops"
    heading = "Azure DevOps"
    asked_every = timedelta(0)

    def __init__(self, az: Az, connect: Callable[[str], Https]):
        self.az = az
        self.connect = connect

    def is_set_up(self) -> bool:
        return self.az.installed()

    def merge_requests(self) -> list[MergeRequest]:
        token = self.az.access_token()
        if not token:
            return []
        api = self.connect(token)
        me = api.get(f"{PROFILES}/profile/profiles/me", **{"api-version": VERSION})["id"]
        reading = ConversationReading(me)
        found = []
        for organisation in api.get(f"{PROFILES}/accounts", memberId=me, **{"api-version": VERSION})["value"]:
            found += self._in(api, organisation["accountName"], reading)
        return found

    def _in(self, api: Https, organisation: str, reading: ConversationReading) -> list[MergeRequest]:
        found = []
        for pull_request in self._pull_requests(api, organisation, "creatorId", reading.me):
            found.append(self._mine(api, organisation, pull_request, reading))
        for pull_request in self._pull_requests(api, organisation, "reviewerId", reading.me):
            found.append(merge_request(organisation, pull_request, self._builds(api, organisation, pull_request), REVIEWING))
        return found

    def _pull_requests(self, api: Https, organisation: str, criterion: str, me: str) -> list[dict]:
        criteria = {f"searchCriteria.{criterion}": me, "searchCriteria.status": "active", "$top": "100", "api-version": VERSION}
        return api.get(f"{organisation_api(organisation)}/git/pullrequests", **criteria)["value"]

    def _mine(self, api: Https, organisation: str, pull_request: dict, reading: ConversationReading) -> MergeRequest:
        found = merge_request(organisation, pull_request, self._builds(api, organisation, pull_request), MINE)
        threads = api.get(f"{pull_request_api(organisation, pull_request)}/threads", **{"api-version": VERSION})["value"]
        commits = api.get(f"{pull_request_api(organisation, pull_request)}/commits", **{"$top": "1", "api-version": VERSION})["value"]
        evaluation = api.post(f"{organisation_api(organisation)}/security/permissionevaluationbatch",
                              _may_contribute(pull_request), **{"api-version": VERSION})
        return replace(found, conversation=reading.conversation(threads, commits), repository=repository_of(evaluation))

    def _builds(self, api: Https, organisation: str, pull_request: dict) -> list[dict]:
        project = pull_request["repository"]["project"]["id"]
        branch = f"refs/pull/{pull_request['pullRequestId']}/merge"
        found = api.get(f"{project_api(organisation, project)}/build/builds", branchName=branch,
                        maxBuildsPerDefinition="1", queryOrder="queueTimeDescending", **{"api-version": VERSION})
        return found["value"]


def _may_contribute(pull_request: dict) -> dict:
    repository = pull_request["repository"]
    token = f"repoV2/{repository['project']['id']}/{repository['id']}"
    return {"alwaysAllowAdministrators": False,
            "evaluations": [{"securityNamespaceId": GIT_REPOSITORIES_SECURITY, "token": token, "permissions": CONTRIBUTE}]}
