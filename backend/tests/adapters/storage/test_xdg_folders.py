import unittest
from pathlib import Path
from unittest import mock

from akari_kopa.adapters.storage.xdg_folders import base_folder

USUAL = Path("/home/someone/.cache")


class XdgFolders(unittest.TestCase):
    def test_an_absolute_folder_given_is_used(self):
        with mock.patch.dict("os.environ", {"XDG_CACHE_HOME": "/elsewhere/cache"}):
            self.assertEqual(base_folder("XDG_CACHE_HOME", USUAL), Path("/elsewhere/cache"))

    def test_a_relative_folder_is_ignored_so_nothing_lands_in_the_current_folder(self):
        with mock.patch.dict("os.environ", {"XDG_CACHE_HOME": "cache"}):
            self.assertEqual(base_folder("XDG_CACHE_HOME", USUAL), USUAL)

    def test_no_folder_given_means_the_usual_one(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(base_folder("XDG_CACHE_HOME", USUAL), USUAL)
