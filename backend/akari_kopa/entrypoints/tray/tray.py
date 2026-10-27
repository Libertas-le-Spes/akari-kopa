from akari_kopa.entrypoints.tray.icon_contents import IconContents
from akari_kopa.presenters.board.board_view import board_view
from akari_kopa.presenters.board.views import BoardView
from akari_kopa.use_cases.desktop.ports import Desktop, Icon, IconContent
from akari_kopa.use_cases.listing.listing import Listing

CHECK_EVERY_SECONDS = 60


class Tray:
    def __init__(self, listing: Listing, desktop: Desktop):
        self.listing = listing
        self.desktop = desktop
        self.contents = IconContents(desktop, self.check)
        self.icons: dict[str, Icon] = {}
        self.checking = False

    def run(self) -> None:
        self.desktop.when_tray_returns(self._register_again)
        self.desktop.every(CHECK_EVERY_SECONDS, self.check)
        self.check()
        self.desktop.run_until_stopped()

    def check(self) -> None:
        if self.checking:
            return
        self.checking = True
        self.desktop.in_background(self._fresh_view, self._show)

    def _fresh_view(self) -> BoardView:
        return board_view(self.listing.board())

    def _show(self, view: BoardView) -> None:
        self.checking = False
        wanted = self.contents.wanted(view)
        for key in _gone(self.icons, wanted):
            self.icons.pop(key).close()
        for key, content in wanted.items():
            self._show_one(key, content)

    def _show_one(self, key: str, content: IconContent) -> None:
        if key in self.icons:
            self.icons[key].update(content)
            return
        self.icons[key] = self.desktop.show_icon(key, content)

    def _register_again(self) -> None:
        for icon in self.icons.values():
            icon.register()


def _gone(icons: dict[str, Icon], wanted: dict[str, IconContent]) -> list[str]:
    gone = []
    for key in icons:
        if key not in wanted:
            gone.append(key)
    return gone
