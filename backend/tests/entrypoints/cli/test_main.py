import contextlib
import io
import unittest

from akari_kopa.entrypoints.cli.main import main


class Main(unittest.TestCase):
    def test_an_unknown_command_names_the_ones_there_are(self):
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            self.assertEqual(main(["dance"]), 2)
        self.assertEqual(errors.getvalue(), "akari-kopa: say one of board, tray, choose, shortcut, remove-shortcut\n")
