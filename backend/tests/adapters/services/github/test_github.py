import unittest

from akari_kopa.adapters.services.github.github import GitHub
from akari_kopa.adapters.transport.graphql_cli import GraphQlCli
from akari_kopa.attention.merge_request.role import MINE, REVIEWING
from akari_kopa.attention.merge_request.web_address import RefusedAddress, WebAddress
from akari_kopa.attention.pipeline.pipeline import NO_PIPELINE, PASSED
from akari_kopa.attention.repository.follow_up import OWN, SOMEONE_ELSES
from tests.fake_command_line import FakeCommandLine
from tests.fakes import on_day

SIGNED_IN = {("gh", "auth", "status"): "github.com\n  ✓ Logged in to github.com\n", ("gh", "auth", "status", "--hostname", "github.com"): ""}


def at(day: float) -> str:
    return on_day(day).strftime("%Y-%m-%dT%H:%M:%SZ")


def person(login: str, kind: str = "User") -> dict:
    return {"__typename": kind, "login": login}


def thread(login: str, day: float, resolved: bool = False) -> dict:
    return {"isResolved": resolved, "comments": {"nodes": [{"author": person(login), "createdAt": at(day)}]}}


def checks(state: str | None) -> dict | None:
    if state is None:
        return None
    return {"state": state}


def pull_request(number: int, permission: str, state: str | None) -> dict:
    return {
        "id": f"PR_{number}", "number": number, "title": f"Change {number}", "url": f"https://github.com/them/thing/pull/{number}",
        "createdAt": at(0), "repository": {"nameWithOwner": "them/thing", "viewerPermission": permission},
        "author": {"login": "me", "name": "Me Myself"},
        "commits": {"nodes": [{"commit": {"committedDate": at(0.5), "statusCheckRollup": checks(state)}}]},
    }


CONVERSATION = {
    "repository": {"viewerPermission": "READ"},
    "reviewThreads": {"pageInfo": {"hasNextPage": True, "endCursor": "c1"}, "nodes": [thread("ana", 2), thread("ana", 0.2, resolved=True)]},
    "comments": {"nodes": [
        {"author": person("ana"), "createdAt": at(2.5)},
        {"author": person("me"), "createdAt": at(3)},
        {"author": person("ci", "Bot"), "createdAt": at(5)},
    ]},
    "reviews": {"nodes": [
        {"author": person("ana"), "state": "COMMENTED", "body": "please rename", "submittedAt": at(4)},
        {"author": person("ana"), "state": "APPROVED", "body": "", "submittedAt": at(6)},
    ]},
}

BOARD = {"data": {
    "viewer": {"login": "me", "pullRequests": {"nodes": [pull_request(1, "READ", None)]}},
    "search": {"nodes": [{**pull_request(9, "WRITE", "SUCCESS"), "author": {"login": "ana", "name": ""}},
                         {**pull_request(10, "WRITE", None), "url": "https://github.com.example.net/them/thing/pull/10"}, {}]},
}}

MORE_THREADS = {"data": {"node": {"reviewThreads": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": [thread("ana", 1)]}}}}


class GitHubTest(unittest.TestCase):
    def setUp(self):
        answers = {("gh", '"after": "c1"'): MORE_THREADS, ("gh", '"id": "PR_1"'): {"data": {"node": CONVERSATION}}, ("gh",): BOARD}
        self.command_line = FakeCommandLine({"gh"}, answers, SIGNED_IN)
        self.found = GitHub(GraphQlCli(self.command_line, "gh", "graphql")).merge_requests()

    def test_my_pull_request_and_the_one_i_review_are_read(self):
        self.assertEqual([(each.reference, each.role, each.author) for each in self.found], [("#1", MINE, "Me Myself"), ("#9", REVIEWING, "ana"), ("#10", REVIEWING, "Me Myself")])

    def test_no_checks_is_no_pipeline_and_success_is_passed(self):
        self.assertEqual([each.pipeline for each in self.found], [NO_PIPELINE, PASSED, NO_PIPELINE])

    def test_a_repository_i_can_only_read_is_someone_elses(self):
        self.assertEqual(self.found[0].repository, SOMEONE_ELSES)
        self.assertEqual(self.found[1].repository, OWN)

    def test_unresolved_threads_are_read_from_every_page(self):
        self.assertEqual(self.found[0].conversation.unresolved_threads, (on_day(2), on_day(1)))

    def test_comments_from_bots_and_approvals_without_words_are_not_waiting(self):
        self.assertEqual(self.found[0].conversation.comments, (on_day(2.5), on_day(4)))

    def test_my_last_answer_is_my_newest_comment_or_commit(self):
        self.assertEqual(self.found[0].conversation.last_answer, on_day(3))
        self.assertEqual(self.found[0].conversation.waiting_since(), on_day(1))

    def test_a_page_on_the_host_asked_can_be_opened(self):
        self.assertEqual(self.found[0].address, WebAddress("https://github.com/them/thing/pull/1", "github.com"))

    def test_a_page_on_any_other_host_is_refused(self):
        self.assertIsInstance(self.found[2].address, RefusedAddress)

    def test_queries_and_their_variables_go_on_standard_input_not_in_arguments(self):
        for arguments in self.command_line.asked:
            self.assertNotIn("PR_1", " ".join(arguments))
        self.assertIn('"id": "PR_1"', " ".join(self.command_line.given))

    def test_nothing_is_asked_when_gh_is_not_installed(self):
        self.assertFalse(GitHub(GraphQlCli(FakeCommandLine(set()), "gh", "graphql")).is_set_up())
