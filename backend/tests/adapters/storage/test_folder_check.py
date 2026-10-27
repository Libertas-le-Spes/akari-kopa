import os
import unittest
from unittest import mock

from akari_kopa.adapters.storage.folder_check import OPEN_FOLDER, FolderRefused, opened_private_folder

OS = "akari_kopa.adapters.storage.folder_check.os"
ME = 1000


def stat_of(uid: int, mode: int) -> mock.Mock:
    return mock.Mock(st_uid=uid, st_mode=0o040000 | mode)


class FolderCheck(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch(OS)
        self.os = patcher.start()
        self.addCleanup(patcher.stop)
        self.os.open.return_value = 7
        self.os.getuid.return_value = ME

    def test_the_folder_is_made_private_opened_without_following_a_link_and_checked_through_that_opening(self):
        self.os.fstat.return_value = stat_of(ME, 0o700)
        self.assertEqual(opened_private_folder("/cache/answers"), 7)
        self.os.makedirs.assert_called_once_with("/cache/answers", mode=0o700, exist_ok=True)
        self.os.open.assert_called_once_with("/cache/answers", OPEN_FOLDER)
        self.os.fstat.assert_called_once_with(7)
        self.os.fchmod.assert_not_called()

    def test_the_opening_refuses_links(self):
        self.assertTrue(OPEN_FOLDER & os.O_NOFOLLOW and OPEN_FOLDER & os.O_DIRECTORY)

    def test_a_folder_of_mine_others_can_reach_is_tightened(self):
        self.os.fstat.return_value = stat_of(ME, 0o777)
        opened_private_folder("/cache/answers")
        self.os.fchmod.assert_called_once_with(7, 0o700)

    def test_a_folder_of_another_account_is_refused_and_closed(self):
        self.os.fstat.return_value = stat_of(ME + 1, 0o700)
        with self.assertRaises(FolderRefused):
            opened_private_folder("/cache/answers")
        self.os.close.assert_called_once_with(7)
        self.os.fchmod.assert_not_called()

    def test_a_link_in_place_of_the_folder_is_refused(self):
        self.os.open.side_effect = OSError(40, "Too many levels of symbolic links")
        with self.assertRaises(FolderRefused):
            opened_private_folder("/cache/answers")
