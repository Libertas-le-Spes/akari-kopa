import unittest

from akari_kopa.adapters.services.gitlab.gitlab import GitLab
from akari_kopa.adapters.transport.graphql_cli import GraphQlCli
from akari_kopa.attention.merge_request.role import MINE, REVIEWING
from akari_kopa.attention.merge_request.web_address import RefusedAddress, WebAddress
from akari_kopa.attention.pipeline.pipeline import FAILED, NO_PIPELINE, PASSED, RUNNING
from akari_kopa.attention.repository.follow_up import OWN, SOMEONE_ELSES
from tests.fake_command_line import FakeCommandLine
from tests.fakes import on_day

SIGNED_IN = {("glab", "auth", "status"): "gitlab.com\n  ✓ Logged in\n", ("glab", "auth", "status", "--hostname", "gitlab.com"): ""}


def at(day: float) -> str:
    return on_day(day).strftime("%Y-%m-%dT%H:%M:%SZ")


def discussion(username: str, day: float, resolvable: bool = True, resolved: bool = False, system: bool = False, bot: bool = False) -> dict:
    note = {"system": system, "createdAt": at(day), "author": {"username": username, "bot": bot}}
    return {"resolvable": resolvable, "resolved": resolved, "notes": {"nodes": [note]}}


def pipeline(status: str | None) -> dict | None:
    if status is None:
        return None
    return {"status": status}


def merge_request(iid: str, status: str | None, can_push: bool) -> dict:
    return {
        "iid": iid, "title": f"Change {iid}", "webUrl": f"https://gitlab.com/team/app/-/merge_requests/{iid}", "createdAt": at(0),
        "project": {"fullPath": "team/app", "userPermissions": {"pushCode": can_push}},
        "author": {"name": "", "username": "me"}, "headPipeline": pipeline(status),
    }


AUTHORED = {
    **merge_request("4", "RUNNING", True),
    "discussions": {"pageInfo": {"hasNextPage": True, "endCursor": "d1"}, "nodes": [
        discussion("me", 1, resolvable=False, system=True),
        discussion("ana", 2),
        discussion("ana", 2.5, resolved=True),
        discussion("renovate", 3, bot=True),
    ]},
}

BOARD = {"data": {"currentUser": {
    "username": "me",
    "authoredMergeRequests": {"nodes": [AUTHORED, {**merge_request("5", "FAILED", False), "discussions": {"pageInfo": {"hasNextPage": False}, "nodes": []}}]},
    "reviewRequestedMergeRequests": {"nodes": [merge_request("6", "MANUAL", True), {**merge_request("7", None, True), "webUrl": "file:///home/someone/.ssh/id_ed25519"}]},
}}}

MORE = {"data": {"project": {"mergeRequest": {"discussions": {"pageInfo": {"hasNextPage": False}, "nodes": [discussion("bo", 4)]}}}}}


class GitLabTest(unittest.TestCase):
    def setUp(self):
        self.command_line = FakeCommandLine({"glab"}, {("glab", '"after": "d1"'): MORE, ("glab",): BOARD}, SIGNED_IN)
        self.found = GitLab(GraphQlCli(self.command_line, "glab", "../graphql")).merge_requests()

    def test_mine_and_the_ones_i_review(self):
        self.assertEqual([(each.reference, each.role, each.author) for each in self.found], [("!4", MINE, "me"), ("!5", MINE, "me"), ("!6", REVIEWING, "me"), ("!7", REVIEWING, "me")])

    def test_a_pipeline_waiting_on_manual_jobs_counts_as_passed(self):
        self.assertEqual([each.pipeline for each in self.found], [RUNNING, FAILED, PASSED, NO_PIPELINE])

    def test_a_project_i_cannot_push_to_is_someone_elses(self):
        self.assertEqual([each.repository for each in self.found[:2]], [OWN, SOMEONE_ELSES])

    def test_open_threads_are_read_from_every_page_leaving_out_bots_and_resolved_ones(self):
        self.assertEqual(self.found[0].conversation.unresolved_threads, (on_day(2), on_day(4)))

    def test_my_pushes_count_as_answers(self):
        self.assertEqual(self.found[0].conversation.last_answer, on_day(1))

    def test_a_page_on_the_host_asked_can_be_opened(self):
        self.assertEqual(self.found[0].address, WebAddress("https://gitlab.com/team/app/-/merge_requests/4", "gitlab.com"))

    def test_a_local_file_is_never_an_address_to_open(self):
        self.assertIsInstance(self.found[3].address, RefusedAddress)

    def test_the_project_paged_through_is_never_put_in_an_argument(self):
        for arguments in self.command_line.asked:
            self.assertNotIn("team/app", " ".join(arguments))
        self.assertIn('"project": "team/app"', " ".join(self.command_line.given))
