import unittest

from akari_kopa.adapters.services.gitea.gitea import Gitea
from akari_kopa.adapters.services.gitea.tea import Tea
from akari_kopa.attention.merge_request.role import MINE, REVIEWING
from akari_kopa.attention.merge_request.web_address import RefusedAddress, WebAddress
from akari_kopa.attention.pipeline.pipeline import NO_PIPELINE, PASSED
from akari_kopa.attention.repository.follow_up import OWN, SOMEONE_ELSES
from tests.fake_command_line import FakeCommandLine
from tests.fakes import on_day, with_value

REPO = "/repos/them/thing"


def at(day: float) -> str:
    return on_day(day).isoformat()


def issue(number: int) -> dict:
    return {"number": number, "title": f"Change {number}", "html_url": f"https://codeberg.org/them/thing/pulls/{number}",
            "repository": {"full_name": "them/thing"}, "user": {"login": "me", "full_name": "Me Myself"}}


def pull(number: int, can_push: bool) -> dict:
    return {"created_at": at(0), "head": {"sha": f"sha{number}"}, "base": {"repo": {"permissions": {"push": can_push}}}}


ANSWERS = {
    ("tea", "logins", "list", "--output", "json"): [{"name": "codeberg", "url": "https://codeberg.org"}],
    ("/user",): {"login": "me"},
    ("/repos/issues/search?type=pulls&state=open&created=true&limit=50",): [issue(1)],
    ("/repos/issues/search?type=pulls&state=open&review_requested=true&limit=50",): [issue(2), with_value(issue(3), "html_url", "smb://203.0.113.9/share")],
    (f"{REPO}/pulls/1",): pull(1, False),
    (f"{REPO}/pulls/2",): pull(2, True),
    (f"{REPO}/pulls/3",): pull(3, True),
    (f"{REPO}/commits/sha3/status",): {"total_count": 0, "state": "pending"},
    (f"{REPO}/commits/sha1/status",): {"total_count": 0, "state": "pending"},
    (f"{REPO}/commits/sha2/status",): {"total_count": 1, "state": "success"},
    (f"{REPO}/pulls/1/reviews",): [{"id": 7, "user": {"login": "ana"}, "state": "REQUEST_CHANGES", "body": "", "submitted_at": at(2)}],
    (f"{REPO}/pulls/1/reviews/7/comments",): [{"user": {"login": "ana"}, "created_at": at(2), "resolver": None},
                                             {"user": {"login": "ana"}, "created_at": at(2.1), "resolver": {"login": "me"}}],
    (f"{REPO}/issues/1/comments",): [{"user": {"login": "ana"}, "created_at": at(3)}, {"user": {"login": "me"}, "created_at": at(4)}],
    (f"{REPO}/git/commits/sha1",): {"commit": {"committer": {"date": at(1)}}},
}


class GiteaTest(unittest.TestCase):
    def setUp(self):
        self.found = Gitea(Tea(FakeCommandLine({"tea"}, ANSWERS))).merge_requests()

    def test_mine_and_the_one_i_review(self):
        self.assertEqual([(each.reference, each.role, each.author) for each in self.found], [("#1", MINE, "Me Myself"), ("#2", REVIEWING, "Me Myself"), ("#3", REVIEWING, "Me Myself")])

    def test_a_commit_with_no_statuses_has_no_pipeline(self):
        self.assertEqual([each.pipeline for each in self.found], [NO_PIPELINE, PASSED, NO_PIPELINE])

    def test_a_repository_i_cannot_push_to_is_someone_elses(self):
        self.assertEqual([each.repository for each in self.found], [SOMEONE_ELSES, OWN, OWN])

    def test_review_comments_nobody_resolved_wait_however_i_answered(self):
        conversation = self.found[0].conversation
        self.assertEqual((conversation.unresolved_threads, conversation.last_answer), ((on_day(2),), on_day(4)))
        self.assertEqual(conversation.waiting_since(), on_day(2))

    def test_a_page_on_the_login_s_own_host_can_be_opened(self):
        self.assertEqual(self.found[0].address, WebAddress("https://codeberg.org/them/thing/pulls/1", "codeberg.org"))

    def test_a_network_share_is_never_an_address_to_open(self):
        self.assertIsInstance(self.found[2].address, RefusedAddress)
