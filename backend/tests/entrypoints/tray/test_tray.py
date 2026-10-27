import unittest

from akari_kopa.attention.merge_request.web_address import RefusedAddress
from akari_kopa.attention.pipeline.pipeline import FAILED
from akari_kopa.entrypoints.tray.tray import Tray
from akari_kopa.use_cases.listing.listing import Listing
from tests.fakes import FORGE_PAGE, Clock, FakeAnswers, FakeService, a_merge_request, on_day

KEY = "forge me/thing #1"


class FakeIcon:
    def __init__(self, content):
        self.content = content
        self.closed = False
        self.registered = 1

    def register(self):
        self.registered += 1

    def update(self, content):
        self.content = content

    def close(self):
        self.closed = True


class FakeDesktop:
    def __init__(self):
        self.icons = {}
        self.notices = []
        self.opened = []

    def show_icon(self, key, content):
        self.icons[key] = FakeIcon(content)
        return self.icons[key]

    def notify(self, summary, body):
        self.notices.append(summary)

    def open_in_browser(self, address):
        self.opened.append(address)

    def in_background(self, work, then):
        then(work())

    def live(self):
        live = {}
        for key, icon in self.icons.items():
            if not icon.closed:
                live[key] = icon
        return live


def entry_named(label, menu):
    for entry in menu:
        if entry.label == label:
            return entry
    raise AssertionError(f"no {label} in the menu")


class TrayTest(unittest.TestCase):
    def setUp(self):
        self.forge = FakeService("forge", a_merge_request())
        self.desktop = FakeDesktop()
        self.tray = Tray(Listing([self.forge], FakeAnswers(), Clock(on_day(1))), self.desktop)

    def test_each_merge_request_gets_its_own_icon(self):
        self.tray.check()
        self.assertEqual(list(self.desktop.live()), [KEY])

    def test_an_icon_changes_in_place_when_its_merge_request_does(self):
        self.tray.check()
        self.forge.answer = [a_merge_request(pipeline=FAILED)]
        self.tray.check()
        icon = self.desktop.live()[KEY]
        self.assertIn("failing", icon.content.description)

    def test_a_merged_merge_request_loses_its_icon(self):
        self.tray.check()
        self.forge.answer = []
        self.tray.check()
        self.assertEqual(self.desktop.live(), {})

    def test_with_nothing_to_show_a_failing_service_still_gets_one_icon_saying_why(self):
        self.forge.answer = []
        self.forge.fails("offline")
        self.tray.check()
        self.assertEqual([icon.content.title for icon in self.desktop.live().values()], ["Not updated: Forge"])

    def test_clicking_open_in_browser_opens_that_merge_request(self):
        self.tray.check()
        entry_named("Open in browser", self.desktop.live()[KEY].content.menu).action()
        self.assertEqual(self.desktop.opened, [FORGE_PAGE])

    def test_clicking_open_in_browser_on_a_refused_address_opens_nothing(self):
        self.forge.answer = [a_merge_request(address=RefusedAddress("only https addresses are opened", "forge.example"))]
        self.tray.check()
        entry_named("Open in browser", self.desktop.live()[KEY].content.menu).action()
        self.assertEqual(self.desktop.opened, [])
