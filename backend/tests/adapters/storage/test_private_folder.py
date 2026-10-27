import os
import unittest
from unittest import mock

from akari_kopa.adapters.storage.folder_check import FolderRefused
from akari_kopa.adapters.storage.private_folder import EXISTING_FILE, NEW_FILE, PRIVATE_FILE, PrivateFolder

PLACE = "akari_kopa.adapters.storage.private_folder"
FOLDER = 7
FILE = 9


class PrivateFolderTest(unittest.TestCase):
    def setUp(self):
        self.os = self._patched("os")
        self.opened_folder = self._patched("opened_private_folder")
        self.opened_folder.return_value = FOLDER
        self.os.open.return_value = FILE
        self.os.getuid.return_value = 1000
        self._patched("secrets").token_hex.return_value = "abc"

    def _patched(self, name: str) -> mock.Mock:
        patcher = mock.patch(f"{PLACE}.{name}")
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_a_write_creates_a_new_private_file_inside_the_checked_folder_then_swaps_it_in(self):
        PrivateFolder("/cache/answers").write("forge.json", "{}")
        self.opened_folder.assert_called_once_with("/cache/answers")
        self.os.open.assert_called_once_with(".forge.json.abc.writing", NEW_FILE, PRIVATE_FILE, dir_fd=FOLDER)
        self.os.fdopen.return_value.__enter__.return_value.write.assert_called_once_with("{}")
        self.os.replace.assert_called_once_with(".forge.json.abc.writing", "forge.json", src_dir_fd=FOLDER, dst_dir_fd=FOLDER)
        self.os.close.assert_called_once_with(FOLDER)

    def test_a_write_that_fails_leaves_no_half_written_file(self):
        self.os.replace.side_effect = OSError("disk full")
        with self.assertRaises(OSError):
            PrivateFolder("/cache/answers").write("forge.json", "{}")
        self.os.unlink.assert_called_once_with(".forge.json.abc.writing", dir_fd=FOLDER)
        self.os.close.assert_called_once_with(FOLDER)

    def test_new_files_are_made_exclusively_without_following_a_link_and_private_from_the_start(self):
        self.assertEqual(NEW_FILE & (os.O_EXCL | os.O_NOFOLLOW | os.O_CREAT), os.O_EXCL | os.O_NOFOLLOW | os.O_CREAT)
        self.assertEqual(PRIVATE_FILE, 0o600)

    def test_existing_files_are_opened_without_following_a_link_or_waiting_on_a_pipe(self):
        self.assertEqual(EXISTING_FILE & (os.O_NOFOLLOW | os.O_NONBLOCK), os.O_NOFOLLOW | os.O_NONBLOCK)

    def test_a_pipe_planted_in_the_folder_is_refused_before_anything_is_read(self):
        self.os.fstat.return_value = mock.Mock(st_uid=1000, st_mode=0o010600)
        with self.assertRaises(FolderRefused):
            PrivateFolder("/cache/answers").read("forge.json")
        self.os.fdopen.return_value.__enter__.return_value.read.assert_not_called()
        self.os.close.assert_called_once_with(FOLDER)

    def test_a_file_of_another_account_planted_in_the_folder_is_refused_before_anything_is_read(self):
        self.os.fstat.return_value = mock.Mock(st_uid=1001, st_mode=0o100600)
        with self.assertRaises(FolderRefused):
            PrivateFolder("/cache/answers").read("forge.json")
        self.os.fdopen.return_value.__enter__.return_value.read.assert_not_called()
        self.os.close.assert_called_once_with(FOLDER)

    def test_a_read_opens_inside_the_checked_folder_without_following_a_link(self):
        self.os.fstat.return_value = mock.Mock(st_uid=1000, st_mode=0o100600)
        self.os.fdopen.return_value.__enter__.return_value.read.return_value = "{}"
        self.assertEqual(PrivateFolder("/cache/answers").read("forge.json"), "{}")
        self.os.open.assert_called_once_with("forge.json", EXISTING_FILE, dir_fd=FOLDER)
        self.os.close.assert_called_once_with(FOLDER)
