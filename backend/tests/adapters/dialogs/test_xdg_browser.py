import unittest

from akari_kopa.adapters.dialogs.xdg_browser import XdgBrowser
from akari_kopa.attention.merge_request.web_address import WebAddress
from tests.fake_command_line import FakeCommandLine


class XdgBrowserTest(unittest.TestCase):
    def test_a_checked_address_is_opened_with_xdg_open(self):
        command_line = FakeCommandLine({"xdg-open"})
        XdgBrowser(command_line).open(WebAddress("https://forge.example/1", "forge.example"))
        self.assertEqual(command_line.asked, [("xdg-open", "https://forge.example/1")])
