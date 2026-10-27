import json
import unittest

from akari_kopa.use_cases.listing.ports import ServiceError

from akari_kopa.adapters.transport.graphql_cli import GraphQlCli
from tests.fake_command_line import FakeCommandLine


class GraphQlCliTest(unittest.TestCase):
    def test_the_query_and_its_variables_are_one_body_on_standard_input(self):
        command_line = FakeCommandLine({"gh"}, {("gh",): {"data": {}}})
        GraphQlCli(command_line, "gh", "graphql").ask("forge.example", "query($id: ID!) { node(id: $id) { id } }", {"id": "made-up"})
        self.assertEqual(command_line.asked, [("gh", "api", "--hostname", "forge.example", "--method", "POST", "--header", "Content-Type: application/json", "graphql", "--input", "-")])
        self.assertEqual(json.loads(command_line.given[0]), {"query": "query($id: ID!) { node(id: $id) { id } }", "variables": {"id": "made-up"}})

    def test_only_hosts_the_tool_is_signed_in_to_are_asked(self):
        said = {("gh", "auth", "status"): "forge.example\n  ✓ Logged in\nother.example\n  X expired\n",
                ("gh", "auth", "status", "--hostname", "forge.example"): ""}
        self.assertEqual(GraphQlCli(FakeCommandLine({"gh"}, said=said), "gh", "graphql").hosts(), ["forge.example"])

    def test_the_endpoint_each_tool_is_given_is_the_one_asked(self):
        command_line = FakeCommandLine({"glab"}, {("glab",): {"data": {}}})
        GraphQlCli(command_line, "glab", "../graphql").ask("forge.example", "query { a }", {})
        self.assertIn("../graphql", command_line.asked[0])

    def test_an_answer_with_errors_is_reported_with_its_first_message(self):
        command_line = FakeCommandLine({"glab"}, {("glab",): {"errors": [{"message": "Field 'x' doesn't exist"}]}})
        with self.assertRaises(ServiceError) as refused:
            GraphQlCli(command_line, "glab", "../graphql").ask("forge.example", "query { x }", {})
        self.assertEqual(refused.exception.reason, "glab: Field 'x' doesn't exist")

    def test_an_answer_with_errors_but_no_message_is_reported_as_refused(self):
        command_line = FakeCommandLine({"glab"}, {("glab",): {"errors": [{"path": ["x"]}]}})
        with self.assertRaises(ServiceError) as refused:
            GraphQlCli(command_line, "glab", "../graphql").ask("forge.example", "query { x }", {})
        self.assertEqual(refused.exception.reason, "glab: the query was refused")
