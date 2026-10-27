from functools import partial
from typing import Callable

from akari_kopa.entrypoints.tray.not_updated_icon import not_updated_entries, only_not_updated
from akari_kopa.presenters.board.views import BoardView, MergeRequestView
from akari_kopa.presenters.orb.pixmap import pixmaps
from akari_kopa.use_cases.desktop.ports import SEPARATOR, Desktop, IconContent, MenuEntry


class IconContents:
    def __init__(self, desktop: Desktop, check_now: Callable[[], None]):
        self.desktop = desktop
        self.check_now = check_now

    def wanted(self, view: BoardView) -> dict[str, IconContent]:
        wanted = {}
        for merge_request in view.merge_requests():
            wanted[merge_request.key] = self._merge_request(merge_request, view)
        if wanted:
            return wanted
        return only_not_updated(view, self.desktop, self.check_now)

    def _merge_request(self, merge_request: MergeRequestView, view: BoardView) -> IconContent:
        description = f"{merge_request.title}\n{merge_request.service} · {merge_request.details}"
        opening = partial(merge_request.address.open_with, self.desktop.open_in_browser)
        return IconContent(
            title=merge_request.summary,
            description=description,
            pixmaps=pixmaps(merge_request.look),
            menu=[
                MenuEntry(merge_request.summary, opening),
                MenuEntry(merge_request.title),
                MenuEntry(f"{merge_request.service} · {merge_request.details}"),
                SEPARATOR,
                MenuEntry("Open in browser", opening),
                MenuEntry("Check now", self.check_now),
            ] + not_updated_entries(view),
            on_activate=partial(self.desktop.notify, merge_request.summary, description),
        )
