import unittest

from merge_requests.adapters.transport.command_line import CommandLine
from merge_requests.use_cases.listing.ports import ServiceError

MISSING = "merge-requests-no-such-tool"


class MissingTools(unittest.TestCase):
    def test_asking_a_missing_tool_gets_no_answer(self):
        self.assertIsNone(CommandLine().answer(MISSING, "reload"))

    def test_needing_a_missing_tool_says_it_is_not_installed(self):
        with self.assertRaises(ServiceError) as refused:
            CommandLine().text(MISSING)
        self.assertEqual(refused.exception.reason, f"{MISSING} is not installed")

    def test_a_tool_that_fails_gives_its_last_words(self):
        with self.assertRaises(ServiceError) as refused:
            CommandLine().text("sh", "-c", "echo first >&2; echo 'last words' >&2; exit 3")
        self.assertEqual(refused.exception.reason, "last words")
