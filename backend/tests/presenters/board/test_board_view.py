import unittest

from merge_requests.attention.merge_request.role import REVIEWING
from merge_requests.presenters.board.board_view import board_view
from merge_requests.use_cases.listing.board import Board, NotUpdated
from tests.fakes import a_merge_request


class BoardView(unittest.TestCase):
    def test_merge_requests_are_grouped_by_role_and_empty_groups_left_out(self):
        view = board_view(Board([a_merge_request(role=REVIEWING, reference="!7", author="Ana")], []))
        self.assertEqual([(group.heading, [each.summary for each in group.merge_requests]) for group in view.groups], [("Reviewing", ["!7 · Ana"])])

    def test_the_details_say_where_whose_and_what_state(self):
        view = board_view(Board([a_merge_request()], []))
        self.assertEqual(view.merge_requests()[0].details, "me/thing · yours · no pipeline")

    def test_a_service_not_updated_fades_every_orb_and_says_why(self):
        view = board_view(Board([a_merge_request()], [NotUpdated("forge", "offline")]))
        self.assertTrue(view.merge_requests()[0].look.faded)
        self.assertEqual((view.not_updated, view.not_updated_summary), (["forge: offline"], "Not updated: forge"))

    def test_the_bar_reads_it_as_plain_json(self):
        raw = board_view(Board([a_merge_request()], [])).as_json()
        self.assertEqual(raw["groups"][0]["merge_requests"][0]["look"], {"colour": "#3fb950", "ring": False, "faded": False})
