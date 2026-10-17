import unittest

from akari_kopa.attention.pipeline.pipeline import FAILED
from akari_kopa.entrypoints.tray.tray import Tray
from akari_kopa.use_cases.listing.listing import Listing
from tests.fakes import Clock, FakeAnswers, FakeService, a_merge_request, on_day


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

    def open_in_browser(self, url):
        self.opened.append(url)

    def in_background(self, work, then):
        then(work())

    def live(self):
        return {key: icon for key, icon in self.icons.items() if not icon.closed}


class TrayTest(unittest.TestCase):
    def setUp(self):
        self.forge = FakeService("forge", a_merge_request(url="https://forge.example/1"))
        self.desktop = FakeDesktop()
        self.tray = Tray(Listing([self.forge], FakeAnswers(), Clock(on_day(1))), self.desktop)

    def test_each_merge_request_gets_its_own_icon(self):
        self.tray.check()
        self.assertEqual(list(self.desktop.live()), ["forge https://forge.example/1"])

    def test_an_icon_changes_in_place_when_its_merge_request_does(self):
        self.tray.check()
        self.forge.answer = [a_merge_request(url="https://forge.example/1", pipeline=FAILED)]
        self.tray.check()
        icon = self.desktop.live()["forge https://forge.example/1"]
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
        menu = self.desktop.live()["forge https://forge.example/1"].content.menu
        next(entry for entry in menu if entry.label == "Open in browser").action()
        self.assertEqual(self.desktop.opened, ["https://forge.example/1"])
