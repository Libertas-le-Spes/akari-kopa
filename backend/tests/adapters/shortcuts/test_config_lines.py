import unittest
from pathlib import Path

from akari_kopa.adapters.shortcuts.config_lines import ConfigLines
from tests.adapters.shortcuts.memory_files import MemoryFiles

PATH = Path("/home/someone/.config/sway/config")


class ConfigLinesTest(unittest.TestCase):
    def setUp(self):
        self.files = MemoryFiles()

    def test_a_line_is_added_on_a_line_of_its_own_to_a_file_that_does_not_end_in_one(self):
        self.files.texts[PATH] = "a = 1"
        ConfigLines(PATH, self.files).add("b = 2")
        self.assertEqual(self.files.texts[PATH], "a = 1\nb = 2\n")

    def test_every_write_says_what_it_read_so_an_edit_made_meanwhile_is_not_lost(self):
        self.files.texts[PATH] = "a = 1\nb = 2 marker\n"
        ConfigLines(PATH, self.files).remove("marker")
        self.assertEqual(self.files.written, [(PATH, "a = 1\nb = 2 marker\n")])
        self.assertEqual(self.files.texts[PATH], "a = 1\n")

    def test_a_missing_file_has_no_line(self):
        self.assertFalse(ConfigLines(PATH, self.files).has("marker"))
