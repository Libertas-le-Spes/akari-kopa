import unittest

from akari_kopa.attention.merge_request.role import REVIEWING
from akari_kopa.attention.merge_request.web_address import RefusedAddress
from akari_kopa.presenters.board.board_view import board_view
from akari_kopa.use_cases.listing.board import Board, NotUpdated
from tests.fakes import a_merge_request


class BoardView(unittest.TestCase):
    def test_merge_requests_are_grouped_by_role_and_empty_groups_left_out(self):
        view = board_view(Board([a_merge_request(role=REVIEWING, reference="!7", author="Ana")], []))
        self.assertEqual([group.heading for group in view.groups], ["Reviewing"])

    def test_within_each_role_merge_requests_are_separated_by_service_under_its_name(self):
        headings = {"gitlab": "GitLab", "github": "GitHub"}
        view = board_view(Board([
            a_merge_request(service="gitlab", reference="!1"),
            a_merge_request(service="github", reference="#2"),
            a_merge_request(service="gitlab", reference="!3"),
            a_merge_request(service="github", role=REVIEWING, reference="#4"),
        ], [], headings))
        self.assertEqual(
            [(group.heading, [(service.heading, [each.summary.split(" ")[0] for each in service.merge_requests]) for service in group.services])
             for group in view.groups],
            [("My merge requests", [("GitLab", ["!1", "!3"]), ("GitHub", ["#2"])]), ("Reviewing", [("GitHub", ["#4"])])],
        )

    def test_each_merge_request_names_its_service_for_flat_lists(self):
        view = board_view(Board([a_merge_request(service="azure-devops")], [], {"azure-devops": "Azure DevOps"}))
        self.assertEqual(view.merge_requests()[0].service, "Azure DevOps")

    def test_the_details_say_where_whose_and_what_state(self):
        view = board_view(Board([a_merge_request()], []))
        self.assertEqual(view.merge_requests()[0].details, "me/thing · yours · no pipeline")

    def test_a_service_not_updated_fades_every_orb_and_says_why(self):
        view = board_view(Board([a_merge_request()], [NotUpdated("forge", "offline")], {"forge": "Forge"}))
        self.assertTrue(view.merge_requests()[0].look.faded)
        self.assertEqual((view.not_updated, view.not_updated_summary), (["Forge: offline"], "Not updated: Forge"))

    def test_the_bar_reads_it_as_plain_json(self):
        raw = board_view(Board([a_merge_request()], [])).as_json()
        self.assertEqual(raw["groups"][0]["services"][0]["merge_requests"][0]["look"], {"colour": "#3fb950", "ring": False, "faded": False})

    def test_each_merge_request_is_known_by_service_project_and_reference_not_by_its_address(self):
        view = board_view(Board([a_merge_request(service="gitlab", project="team/app", reference="!4")], []))
        self.assertEqual(view.merge_requests()[0].key, "gitlab team/app !4")

    def test_an_address_that_was_refused_says_why_in_the_details(self):
        refused = RefusedAddress("only https addresses are opened", "forge.example")
        view = board_view(Board([a_merge_request(address=refused)], []))
        self.assertEqual(view.merge_requests()[0].details, "me/thing · yours · no pipeline · not opened: only https addresses are opened")

    def test_the_bar_gets_the_address_text_and_nothing_for_a_refused_one(self):
        refused = RefusedAddress("only https addresses are opened", "forge.example")
        raw = board_view(Board([a_merge_request(), a_merge_request(reference="#2", address=refused)], [])).as_json()
        addresses = []
        for merge_request in raw["groups"][0]["services"][0]["merge_requests"]:
            addresses.append(merge_request["address"]["text"])
        self.assertEqual(addresses, ["https://forge.example/1", ""])
