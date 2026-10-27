import unittest

from akari_kopa.adapters.desktop.markup import NOTICE_MILLISECONDS, notice, tool_tip
from akari_kopa.use_cases.desktop.ports import IconContent

TITLE = '<b>x</b><img src="https://example.invalid/p.png"/>'
ESCAPED = "&lt;b&gt;x&lt;/b&gt;&lt;img src=&quot;https://example.invalid/p.png&quot;/&gt;"


class Markup(unittest.TestCase):
    def test_a_notice_body_is_escaped_and_its_plain_text_summary_left_alone(self):
        self.assertEqual(notice("#1 · Me", TITLE), ("Akari Kopa", 0, "", "#1 · Me", ESCAPED, [], {}, NOTICE_MILLISECONDS))

    def test_a_tool_tip_escapes_its_title_and_description(self):
        content = IconContent(title=TITLE, description=TITLE, pixmaps=[], menu=[])
        self.assertEqual(tool_tip(content), ("", [], ESCAPED, ESCAPED))
