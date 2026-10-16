import unittest

from akari_kopa.adapters.transport.command_line import CommandLine
from akari_kopa.use_cases.listing.ports import ServiceError

MISSING = "akari-kopa-no-such-tool"


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
