import subprocess
import unittest
from unittest import mock

from akari_kopa.adapters.transport.command_line import TIMEOUT_SECONDS, CommandLine
from akari_kopa.use_cases.listing.ports import ServiceError

RUN = "akari_kopa.adapters.transport.command_line.subprocess.run"
WHICH = "akari_kopa.adapters.transport.command_line.shutil.which"


def finished(code: int = 0, said: str = "", errors: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], code, said, errors)


class CommandLineTest(unittest.TestCase):
    def setUp(self):
        which = mock.patch(WHICH, return_value="/usr/bin/tool")
        self.which = which.start()
        self.addCleanup(which.stop)

    def test_text_is_handed_over_on_standard_input_with_a_time_limit(self):
        with mock.patch(RUN, return_value=finished(said="{}")) as run:
            CommandLine().json("tool", "api", given='{"query": "q"}')
        run.assert_called_once_with(("tool", "api"), input='{"query": "q"}', stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, timeout=TIMEOUT_SECONDS)

    def test_a_tool_given_nothing_gets_an_empty_input_not_the_callers(self):
        with mock.patch(RUN, return_value=finished()) as run:
            CommandLine().text("tool")
        self.assertEqual(run.call_args.kwargs["input"], "")

    def test_a_tool_that_never_answers_is_reported_not_waited_on(self):
        with mock.patch(RUN, side_effect=subprocess.TimeoutExpired("tool", TIMEOUT_SECONDS)):
            with self.assertRaises(ServiceError) as refused:
                CommandLine().text("tool")
        self.assertEqual(refused.exception.reason, f"tool did not answer within {TIMEOUT_SECONDS} seconds")

    def test_a_tool_that_fails_gives_its_last_words(self):
        with mock.patch(RUN, return_value=finished(3, errors="first\n\nlast words\n")):
            with self.assertRaises(ServiceError) as refused:
                CommandLine().text("tool")
        self.assertEqual(refused.exception.reason, "last words")

    def test_a_tool_that_fails_silently_is_named(self):
        with mock.patch(RUN, return_value=finished(3)):
            with self.assertRaises(ServiceError) as refused:
                CommandLine().text("tool")
        self.assertEqual(refused.exception.reason, "tool failed")

    def test_needing_a_missing_tool_says_it_is_not_installed(self):
        self.which.return_value = None
        with mock.patch(RUN) as run, self.assertRaises(ServiceError) as refused:
            CommandLine().text("tool")
        self.assertEqual(refused.exception.reason, "tool is not installed")
        run.assert_not_called()

    def test_a_choice_waits_for_the_person_with_no_time_limit(self):
        with mock.patch(RUN, return_value=finished(said="picked\n")) as run:
            self.assertEqual(CommandLine().chosen("rows\n", "dialog", "--list"), "picked")
        run.assert_called_once_with(("dialog", "--list"), input="rows\n", capture_output=True, text=True)
