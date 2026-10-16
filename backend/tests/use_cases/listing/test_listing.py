import unittest
from dataclasses import replace
from datetime import timedelta

from akari_kopa.attention.repository.follow_up import SOMEONE_ELSES
from akari_kopa.use_cases.listing.listing import Listing
from tests.fakes import Clock, FakeAnswers, FakeService, a_merge_request, on_day


class Board(unittest.TestCase):
    def setUp(self):
        self.clock = Clock(on_day(1))
        self.answers = FakeAnswers()

    def listing(self, *services):
        return Listing(list(services), self.answers, self.clock)

    def test_every_set_up_service_is_asked_and_their_answers_are_put_together(self):
        board = self.listing(FakeService("forge", a_merge_request(reference="#1")), FakeService("hub", a_merge_request(reference="#2"))).board()
        self.assertEqual([found.reference for found in board.merge_requests], ["#1", "#2"])
        self.assertEqual(board.not_updated, [])

    def test_a_service_that_is_not_set_up_is_not_asked(self):
        unused = FakeService("forge", a_merge_request())
        unused.set_up = False
        self.assertEqual(self.listing(unused).board().merge_requests, [])
        self.assertEqual(unused.times_asked, 0)

    def test_a_service_that_fails_shows_its_last_answer_and_says_why(self):
        forge = FakeService("forge", a_merge_request())
        listing = self.listing(forge)
        listing.board()
        forge.fails("forge.example refused the request: 401 Unauthorized")
        board = listing.board()
        self.assertEqual(len(board.merge_requests), 1)
        self.assertEqual([(each.service, each.reason) for each in board.not_updated], [("forge", "forge.example refused the request: 401 Unauthorized")])

    def test_an_unexpected_answer_is_reported_instead_of_stopping_every_service(self):
        broken, working = FakeService("broken"), FakeService("forge", a_merge_request())
        broken.failure = KeyError("pageInfo")
        board = self.listing(broken, working).board()
        self.assertEqual(len(board.merge_requests), 1)
        self.assertEqual(board.not_updated[0].reason, "unexpected answer: KeyError 'pageInfo'")

    def test_a_service_asked_less_often_is_answered_from_its_last_answer_in_between(self):
        slow = FakeService("slow", a_merge_request(), asked_every=timedelta(minutes=5))
        listing = self.listing(slow)
        listing.board()
        self.clock.now += timedelta(minutes=4)
        listing.board()
        self.clock.now += timedelta(minutes=2)
        listing.board()
        self.assertEqual(slow.times_asked, 2)

    def test_one_resting_in_someone_elses_repository_is_left_off(self):
        resting = a_merge_request(repository=SOMEONE_ELSES)
        self.clock.now = on_day(4)
        self.assertEqual(self.listing(FakeService("forge", resting)).board().merge_requests, [])


class AMadeUpService(unittest.TestCase):
    def test_a_new_kind_of_service_needs_nothing_but_its_own_class(self):
        class Notebook:
            name = "notebook"
            asked_every = timedelta(0)

            def is_set_up(self):
                return True

            def merge_requests(self):
                return [replace(a_merge_request(), service="notebook", reference="page 4")]

        board = Listing([Notebook()], FakeAnswers(), Clock(on_day(1))).board()
        self.assertEqual([(each.service, each.reference) for each in board.merge_requests], [("notebook", "page 4")])
