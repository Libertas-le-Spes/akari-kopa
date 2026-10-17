from akari_kopa.presenters.board.board_view import BoardView, board_view
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
            return "akari-kopa: install zenity or kdialog to choose a merge request from a list"
        view = self._view()
        options = [Option(mr.key, mr.summary, f"{mr.title} · {mr.service} · {mr.details}") for mr in view.merge_requests()]
        chosen = self.chooser.choose(TITLE, _question(options), options)
        self._open(view, chosen)
        return ""

    def _view(self) -> BoardView:
        remembered = self.listing.remembered()
        return board_view(remembered if remembered.merge_requests else self.listing.board())

    def _open(self, view: BoardView, chosen: str | None) -> None:
        url = next((mr.url for mr in view.merge_requests() if mr.key == chosen), None)
        if url:
            self.browser.open(url)


def _question(options: list[Option]) -> str:
    return "Open which one?" if options else "No open merge requests right now."
