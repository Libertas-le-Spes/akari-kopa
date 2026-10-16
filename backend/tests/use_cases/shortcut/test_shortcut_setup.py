import unittest

from merge_requests.use_cases.shortcut.shortcut_setup import NoShortcutHome, ShortcutSetup


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
        self.assertEqual(ShortcutSetup([elsewhere, here, also_here]).add(), "Super + Ctrl + M now opens your merge requests (Here).")
        self.assertEqual((elsewhere.set, here.set, also_here.set), (False, True, False))

    def test_setting_it_twice_changes_nothing(self):
        self.assertEqual(ShortcutSetup([MadeUpDesktop("Here", True, has_it=True)]).add(), "Super + Ctrl + M already opens your merge requests (Here).")

    def test_a_desktop_nobody_knows_says_which_ones_are_known(self):
        with self.assertRaises(NoShortcutHome) as refused:
            ShortcutSetup([MadeUpDesktop("Plasma", False), MadeUpDesktop("Xfce", False)]).add()
        self.assertIn("(Plasma, Xfce)", str(refused.exception))

    def test_removing_takes_it_out_wherever_it_was_set(self):
        here = MadeUpDesktop("Here", True, has_it=True)
        self.assertEqual(ShortcutSetup([here]).remove(), "Removed the shortcut (Here).")
        self.assertFalse(here.set)
        self.assertEqual(ShortcutSetup([here]).remove(), "There was no shortcut to remove.")
