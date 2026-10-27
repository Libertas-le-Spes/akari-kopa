import unittest
from unittest import mock

from akari_kopa.adapters.shortcuts.text_files import NEW_FILE, NEW_FILE_MODE, TextFiles
from akari_kopa.use_cases.shortcut.ports import ShortcutRefused

PLACE = "akari_kopa.adapters.shortcuts.text_files"


class TextFilesTest(unittest.TestCase):
    def setUp(self):
        self.os = self._patched("os")
        self.os.open.return_value = 9
        self._patched("secrets").token_hex.return_value = "abc"
        self.linked = mock.MagicMock(name="linked dotfile")
        self.target = self.linked.resolve.return_value
        self.writing = self.target.parent.__truediv__.return_value
        self.target.name = "hyprland.conf"
        self.target.read_text.return_value = "old\n"
        self.target.stat.return_value.st_mode = 0o100640

    def _patched(self, name: str) -> mock.Mock:
        patcher = mock.patch(f"{PLACE}.{name}")
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_the_file_a_link_leads_to_is_replaced_whole_so_the_link_stays_a_link(self):
        TextFiles().write_whole(self.linked, "new\n", was="old\n")
        self.target.parent.__truediv__.assert_called_once_with(".hyprland.conf.abc.writing")
        self.os.open.assert_called_once_with(self.writing, NEW_FILE, 0o640)
        self.os.fdopen.return_value.__enter__.return_value.write.assert_called_once_with("new\n")
        self.os.replace.assert_called_once_with(self.writing, self.target)

    def test_a_new_file_gets_the_usual_permissions(self):
        self.target.exists.return_value = False
        TextFiles().write_whole(self.linked, "new\n", was=None)
        self.os.open.assert_called_once_with(self.writing, NEW_FILE, NEW_FILE_MODE)

    def test_a_file_changed_since_it_was_read_is_left_as_it_is(self):
        self.target.read_text.return_value = "edited meanwhile\n"
        with self.assertRaises(ShortcutRefused):
            TextFiles().write_whole(self.linked, "new\n", was="old\n")
        self.os.open.assert_not_called()
        self.os.replace.assert_not_called()

    def test_a_write_that_fails_leaves_no_half_written_file(self):
        self.os.replace.side_effect = OSError("disk full")
        with self.assertRaises(OSError):
            TextFiles().write_whole(self.linked, "new\n", was="old\n")
        self.os.unlink.assert_called_once_with(self.writing)
