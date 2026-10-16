import unittest

from merge_requests.entrypoints.choose.choose import Choose
from merge_requests.use_cases.listing.listing import Listing
from tests.fakes import Clock, FakeAnswers, FakeService, a_merge_request, on_day


class FakeChooser:
    name = "fake"

    def __init__(self, picks: str | None):
        self.picks = picks
        self.shown = None

    def installed(self):
        return True

    def choose(self, title, question, options):
        self.shown = (question, [option.label for option in options])
        return self.picks


class FakeBrowser:
    def __init__(self):
        self.opened = []

    def open(self, url):
        self.opened.append(url)


class ChooseTest(unittest.TestCase):
    def setUp(self):
        self.forge = FakeService("forge", a_merge_request(url="https://forge.example/1", reference="#1", author="Me"))
        self.listing = Listing([self.forge], FakeAnswers(), Clock(on_day(1)))
        self.browser = FakeBrowser()

    def test_the_one_picked_opens_in_the_browser(self):
        Choose(self.listing, FakeChooser("forge https://forge.example/1"), self.browser).run()
        self.assertEqual(self.browser.opened, ["https://forge.example/1"])

    def test_closing_the_list_opens_nothing(self):
        Choose(self.listing, FakeChooser(None), self.browser).run()
        self.assertEqual(self.browser.opened, [])

    def test_the_last_answers_are_shown_at_once_without_asking_again(self):
        self.listing.board()
        chooser = FakeChooser(None)
        Choose(self.listing, chooser, self.browser).run()
        self.assertEqual((self.forge.times_asked, chooser.shown), (1, ("Open which one?", ["#1 · Me"])))

    def test_with_nothing_open_it_says_so(self):
        self.forge.answer = []
        chooser = FakeChooser(None)
        Choose(self.listing, chooser, self.browser).run()
        self.assertEqual(chooser.shown, ("No open merge requests right now.", []))

    def test_without_a_list_dialog_it_says_what_to_install(self):
        self.assertIn("zenity or kdialog", Choose(self.listing, None, self.browser).run())
