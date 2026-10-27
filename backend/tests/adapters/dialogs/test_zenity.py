import unittest

from akari_kopa.adapters.dialogs.zenity import Zenity
from akari_kopa.use_cases.choosing.ports import Option
from tests.fake_command_line import FakeCommandLine

COLUMNS = ("zenity", "--list", "--title=Akari Kopa", "--text=Open which one?", "--width=760", "--height=420",
           "--column=key", "--column=Merge request", "--column=Details", "--hide-column=1", "--print-column=1")


class ZenityTest(unittest.TestCase):
    def setUp(self):
        self.command_line = FakeCommandLine({"zenity"}, said={COLUMNS: "forge me/thing #1"})
        self.options = [Option("forge me/thing #1", "#1 · Me", "Acquire Example Corp quietly\nsecond line · forge")]

    def test_rows_go_on_standard_input_one_cell_per_line_and_never_in_arguments(self):
        Zenity(self.command_line).choose("Akari Kopa", "Open which one?", self.options)
        self.assertEqual(self.command_line.asked, [COLUMNS])
        self.assertEqual(self.command_line.given, ["forge me/thing #1\n#1 · Me\nAcquire Example Corp quietly second line · forge\n"])

    def test_the_key_of_the_row_picked_comes_back(self):
        self.assertEqual(Zenity(self.command_line).choose("Akari Kopa", "Open which one?", self.options), "forge me/thing #1")
