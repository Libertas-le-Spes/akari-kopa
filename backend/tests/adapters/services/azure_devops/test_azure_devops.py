import unittest

from akari_kopa.adapters.services.azure_devops.az import AZURE_DEVOPS, Az
from akari_kopa.adapters.services.azure_devops.azure_devops import AzureDevOps
from akari_kopa.adapters.services.moment import moment
from akari_kopa.attention.merge_request.role import MINE, REVIEWING
from akari_kopa.attention.pipeline.pipeline import FAILED, RUNNING
from akari_kopa.attention.repository.follow_up import SOMEONE_ELSES
from tests.fakes import FakeCommandLine, on_day

ORG = "https://dev.azure.com/contoso"
PULL_REQUEST = f"{ORG}/p1/_apis/git/repositories/r1/pullRequests"
TOKEN = ("az", "account", "get-access-token", "--resource", AZURE_DEVOPS, "--query", "accessToken", "--output", "tsv")


def at(day: float) -> str:
    return on_day(day).strftime("%Y-%m-%dT%H:%M:%S.1234567Z")


def pull_request(number: int, author: str) -> dict:
    return {"pullRequestId": number, "title": f"Change {number}", "creationDate": at(0), "createdBy": {"displayName": author},
            "repository": {"id": "r1", "name": "Web App", "project": {"id": "p1", "name": "Shop"}}}


def thread(author: str, day: float, status: str | None, kind: str = "text") -> dict:
    found = {"comments": [{"author": {"id": author}, "publishedDate": at(day), "commentType": kind}]}
    return {**found, "status": status} if status else found


GETS = {
    "https://app.vssps.visualstudio.com/_apis/profile/profiles/me": {"id": "me"},
    "https://app.vssps.visualstudio.com/_apis/accounts": {"value": [{"accountName": "contoso"}]},
    f"{ORG}/p1/_apis/build/builds 7": {"value": [{"status": "inProgress"}, {"status": "completed", "result": "succeeded"}]},
    f"{ORG}/p1/_apis/build/builds 8": {"value": [{"status": "completed", "result": "failed"}]},
    f"{PULL_REQUEST}/7/threads": {"value": [
        thread("ana", 2, "active"),
        thread("ana", 2.5, "fixed"),
        thread("ana", 3, None),
        thread("ana", 0.1, None, kind="system"),
        thread("me", 3.5, "active"),
    ]},
    f"{PULL_REQUEST}/7/commits": {"value": [{"committer": {"date": at(1)}}]},
}


class FakeHttps:
    def __init__(self, base: str, token: str):
        self.token = token
        self.posted = []

    def get(self, path: str, **parameters: str):
        if "searchCriteria.creatorId" in parameters:
            return {"value": [pull_request(7, "Me Myself")]}
        if "searchCriteria.reviewerId" in parameters:
            return {"value": [pull_request(8, "Ana")]}
        number = parameters.get("branchName", "").split("/")[2] if "branchName" in parameters else ""
        return GETS[f"{path} {number}".strip()]

    def post(self, path: str, body: dict, **parameters: str):
        self.posted.append(body["evaluations"][0]["token"])
        return {"evaluations": [{"value": False}]}


def az(installed: bool = True, token: str | None = "token") -> Az:
    said = {TOKEN: token} if token else {}
    return Az(FakeCommandLine({"az"} if installed else set(), said=said))


class AzureDevOpsTest(unittest.TestCase):
    def setUp(self):
        self.connected = []
        self.found = AzureDevOps(az(), self._connect).merge_requests()

    def _connect(self, base, token):
        self.connected.append(FakeHttps(base, token))
        return self.connected[-1]

    def test_the_token_az_gives_is_the_one_sent(self):
        self.assertEqual(self.connected[0].token, "token")

    def test_mine_and_the_one_i_review_in_every_organisation(self):
        self.assertEqual([(each.reference, each.role, each.author) for each in self.found], [("!7", MINE, "Me Myself"), ("!8", REVIEWING, "Ana")])
        self.assertEqual(self.found[0].url, "https://dev.azure.com/contoso/Shop/_git/Web%20App/pullrequest/7")

    def test_a_build_still_going_is_running_and_a_failed_one_fails_it(self):
        self.assertEqual([each.pipeline for each in self.found], [RUNNING, FAILED])

    def test_without_contribute_permission_it_is_someone_elses_repository(self):
        self.assertEqual(self.found[0].repository, SOMEONE_ELSES)
        self.assertEqual(self.connected[0].posted, ["repoV2/p1/r1"])

    def test_active_threads_wait_status_less_comments_wait_for_an_answer_and_system_ones_never(self):
        conversation = self.found[0].conversation
        self.assertEqual((conversation.unresolved_threads, conversation.comments), ((moment(at(2)),), (moment(at(3)),)))
        self.assertEqual(conversation.last_answer, moment(at(3.5)))

    def test_without_az_it_is_not_set_up(self):
        self.assertFalse(AzureDevOps(az(installed=False), FakeHttps).is_set_up())

    def test_with_az_not_logged_in_nothing_is_asked_of_azure_devops(self):
        self.assertEqual(AzureDevOps(az(token=None), self._connect).merge_requests(), [])
        self.assertEqual(len(self.connected), 1)
