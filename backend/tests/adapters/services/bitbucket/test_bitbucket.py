import unittest

from merge_requests.adapters.services.bitbucket.bitbucket import Bitbucket
from merge_requests.attention.merge_request.role import MINE, REVIEWING
from merge_requests.attention.pipeline.pipeline import FAILED, NO_PIPELINE
from merge_requests.attention.repository.follow_up import SOMEONE_ELSES
from tests.fakes import Clock, on_day

PULLS = "/repositories/them/thing/pullrequests"


def at(day: float) -> str:
    return on_day(day).isoformat()


def pull_request(number: int) -> dict:
    return {"id": number, "title": f"Change {number}", "links": {"html": {"href": f"https://bitbucket.org/them/thing/pull-requests/{number}"}},
            "destination": {"repository": {"full_name": "them/thing"}}, "author": {"display_name": "Me Myself"}, "created_on": at(0)}


GETS = {"/user": {"uuid": "{me}"}, f"{PULLS}/1/commits": {"values": [{"date": at(1)}]}}

PAGES = {
    "/user/workspaces": [{"workspace": {"slug": "them"}}],
    "/workspaces/them/pullrequests/{me}": [pull_request(1)],
    "/repositories/them": [{"full_name": "them/thing"}],
    PULLS: [pull_request(2)],
    f"{PULLS}/1/statuses": [],
    f"{PULLS}/2/statuses": [{"state": "SUCCESSFUL"}, {"state": "FAILED"}],
    f"{PULLS}/1/comments": [
        {"user": {"uuid": "{ana}"}, "created_on": at(2), "inline": {"path": "a.py"}},
        {"user": {"uuid": "{ana}"}, "created_on": at(2.5), "inline": {"path": "b.py"}, "resolution": {"type": "resolved"}},
        {"user": {"uuid": "{me}"}, "created_on": at(3), "parent": {"id": 1}},
        {"user": {"uuid": "{ana}"}, "created_on": at(4)},
    ],
    "/user/permissions/repositories": [{"permission": "read"}],
}


class FakeHttps:
    def __init__(self, base: str, credentials: str):
        self.credentials = credentials

    def get(self, path: str, **parameters: str):
        return GETS[path]

    def pages(self, path: str, **parameters: str) -> list:
        return PAGES[path]


class FakeKeyring:
    def __init__(self, stored: str):
        self.stored = stored

    def lookup(self, attribute: str, value: str) -> str:
        return self.stored


class BitbucketTest(unittest.TestCase):
    def setUp(self):
        self.found = Bitbucket(FakeKeyring("me@example.com:token"), FakeHttps, Clock(on_day(5))).merge_requests()

    def test_mine_and_the_one_i_review(self):
        self.assertEqual([(each.reference, each.role) for each in self.found], [("#1", MINE), ("#2", REVIEWING)])

    def test_no_statuses_is_no_pipeline_and_any_failed_one_fails_it(self):
        self.assertEqual([each.pipeline for each in self.found], [NO_PIPELINE, FAILED])

    def test_read_permission_only_is_someone_elses_repository(self):
        self.assertEqual(self.found[0].repository, SOMEONE_ELSES)

    def test_open_inline_threads_wait_and_plain_comments_wait_for_an_answer(self):
        conversation = self.found[0].conversation
        self.assertEqual((conversation.unresolved_threads, conversation.comments, conversation.last_answer), ((on_day(2),), (on_day(4),), on_day(3)))

    def test_without_a_key_in_the_keyring_it_is_not_set_up(self):
        self.assertFalse(Bitbucket(FakeKeyring(""), FakeHttps, Clock()).is_set_up())
