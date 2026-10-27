from akari_kopa.presenters.board.board_view import board_view
from akari_kopa.presenters.board.views import BoardView
from akari_kopa.use_cases.choosing.ports import Browser, Chooser, Option
from akari_kopa.use_cases.listing.listing import Listing

TITLE = "Akari Kopa"


class Choose:
    def __init__(self, listing: Listing, chooser: Chooser | None, browser: Browser):
        self.listing = listing
        self.chooser = chooser
        self.browser = browser

    def run(self) -> str:
        if self.chooser is None:
            return "akari-kopa: install zenity to choose a merge request from a list"
        view = self._view()
        options = _options(view)
        chosen = view.find(self.chooser.choose(TITLE, _question(options), options))
        if chosen is not None:
            chosen.address.open_with(self.browser.open)
        return ""

    def _view(self) -> BoardView:
        remembered = self.listing.remembered()
        if remembered.merge_requests:
            return board_view(remembered)
        return board_view(self.listing.board())


def _options(view: BoardView) -> list[Option]:
    options = []
    for merge_request in view.merge_requests():
        detail = f"{merge_request.title} · {merge_request.service} · {merge_request.details}"
        options.append(Option(merge_request.key, merge_request.summary, detail))
    return options


def _question(options: list[Option]) -> str:
    if options:
        return "Open which one?"
    return "No open merge requests right now."
