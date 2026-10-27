import re
import unittest

from tests.source_files import REPOSITORY, relative

PINNED = re.compile(r"uses:\s*[\w.-]+/[\w./-]+@[0-9a-f]{40}\s*$")


def workflows() -> dict[str, str]:
    found = {}
    for path in sorted((REPOSITORY / ".github" / "workflows").glob("*.yml")):
        found[relative(path)] = path.read_text(encoding="utf-8")
    return found


def uses_lines(text: str) -> list[str]:
    found = []
    for line in text.splitlines():
        if "uses:" in line:
            found.append(line.strip().removeprefix("- "))
    return found


class Workflows(unittest.TestCase):
    def test_there_is_a_workflow_to_check(self):
        self.assertNotEqual(workflows(), {})

    def test_no_workflow_runs_code_from_a_fork_with_this_repository_s_rights(self):
        for name, text in workflows().items():
            with self.subTest(name):
                self.assertNotIn("pull_request_target", text)
                self.assertNotIn("secrets.", text)

    def test_every_workflow_asks_only_to_read(self):
        for name, text in workflows().items():
            with self.subTest(name):
                self.assertIn("\npermissions:\n  contents: read\n", text)

    def test_every_action_is_pinned_to_a_full_commit(self):
        for name, text in workflows().items():
            for line in uses_lines(text):
                with self.subTest(name, line=line):
                    self.assertRegex(line, PINNED)
