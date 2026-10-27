import unittest

from akari_kopa.use_cases.shortcut.ports import ShortcutRefused
from akari_kopa.use_cases.shortcut.shortcut_setup import NoShortcutHome, ShortcutSetup

SAFE = "/home/someone/.config/omarchy/plugins/kayu.akari-kopa"


class MadeUpDesktop:
    def __init__(self, name: str, here: bool, has_it: bool = False):
        self.name = name
        self.is_here = here
        self.set = has_it

    def here(self):
        return self.is_here

    def has_it(self):
        return self.set

    def add(self):
        self.set = True

    def remove(self):
        self.set = False


class ShortcutSetupTest(unittest.TestCase):
    def test_the_first_desktop_that_is_here_gets_the_shortcut(self):
        elsewhere, here, also_here = MadeUpDesktop("Elsewhere", False), MadeUpDesktop("Here", True), MadeUpDesktop("Also", True)
        self.assertEqual(ShortcutSetup([elsewhere, here, also_here], SAFE).add(), "Super + Ctrl + M now opens your merge requests (Here).")
        self.assertEqual((elsewhere.set, here.set, also_here.set), (False, True, False))

    def test_setting_it_twice_changes_nothing(self):
        self.assertEqual(ShortcutSetup([MadeUpDesktop("Here", True, has_it=True)], SAFE).add(), "Super + Ctrl + M already opens your merge requests (Here).")

    def test_a_desktop_nobody_knows_says_which_ones_are_known(self):
        with self.assertRaises(NoShortcutHome) as refused:
            ShortcutSetup([MadeUpDesktop("Plasma", False), MadeUpDesktop("Xfce", False)], SAFE).add()
        self.assertIn("(Plasma, Xfce)", str(refused.exception))

    def test_removing_takes_it_out_wherever_it_was_set(self):
        here = MadeUpDesktop("Here", True, has_it=True)
        self.assertEqual(ShortcutSetup([here], SAFE).remove(), "Removed the shortcut (Here).")
        self.assertFalse(here.set)
        self.assertEqual(ShortcutSetup([here], SAFE).remove(), "There was no shortcut to remove.")

    def test_an_install_folder_whose_name_could_be_read_as_a_command_gets_no_shortcut(self):
        here = MadeUpDesktop("Here", True)
        for folder in ('/home/someone/odd $(touch /tmp/x)") os.execute("id")--', "/home/some one/akari-kopa", "/opt/akari%u"):
            with self.subTest(folder), self.assertRaises(ShortcutRefused):
                ShortcutSetup([here], folder).add()
        self.assertFalse(here.set)
