import ast
import unittest

from tests.source_files import PACKAGE, REPOSITORY, files_saying, read

OPENERS = {
    "xdg-open": ["backend/akari_kopa/adapters/dialogs/xdg_browser.py"],
    "launch_default_for_uri": ["backend/akari_kopa/adapters/desktop/linux_desktop.py"],
    "openUrlExternally": ["frontend/omarchy-bar/BarWidget.qml"],
}
ADDRESS_MAKERS = ["backend/akari_kopa/attention/merge_request/address_check.py"]


def annotation_of(source: str, method: str) -> str:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == method:
            return ast.unparse(node.args.args[1].annotation)
    raise AssertionError(f"no method {method}")


class Openers(unittest.TestCase):
    def test_only_the_opener_adapters_hand_anything_to_the_desktop_to_open(self):
        for opener, allowed in OPENERS.items():
            with self.subTest(opener):
                found = files_saying(opener, PACKAGE, "*.py") + files_saying(opener, REPOSITORY / "frontend", "*.qml")
                self.assertEqual(found, allowed)

    def test_the_openers_take_only_a_checked_address(self):
        self.assertEqual(annotation_of(read("backend/akari_kopa/use_cases/choosing/ports.py"), "open"), "WebAddress")
        self.assertEqual(annotation_of(read("backend/akari_kopa/use_cases/desktop/ports.py"), "open_in_browser"), "WebAddress")

    def test_only_the_check_makes_an_address_that_can_be_opened(self):
        self.assertEqual(files_saying("WebAddress(text", PACKAGE, "*.py"), ADDRESS_MAKERS)

    def test_the_bar_opens_nothing_that_is_not_a_web_page(self):
        widget = read("frontend/omarchy-bar/BarWidget.qml")
        self.assertIn('return typeof address === "string" && address.indexOf("https://") === 0', widget)
        self.assertIn("if (isWebPage(address)) Qt.openUrlExternally(address)", widget)
        self.assertEqual(widget.count("openUrlExternally"), 1)
