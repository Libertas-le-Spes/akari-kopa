from typing import Callable

from akari_kopa.presenters.board.board_view import BoardView, MergeRequestView
from akari_kopa.presenters.orb.pixmap import pixmaps
from akari_kopa.use_cases.desktop.ports import SEPARATOR, Desktop, IconContent, MenuEntry


class IconContents:
    def __init__(self, desktop: Desktop, check_now: Callable[[], None]):
        self.desktop = desktop
        self.check_now = check_now

    def wanted(self, view: BoardView) -> dict[str, IconContent]:
        wanted = {merge_request.key: self._merge_request(merge_request, view) for merge_request in view.merge_requests()}
        return wanted or self._only_not_updated(view)

    def _merge_request(self, merge_request: MergeRequestView, view: BoardView) -> IconContent:
        description = f"{merge_request.title}\n{merge_request.details}"
        opening = lambda: self.desktop.open_in_browser(merge_request.url)
        return IconContent(
            title=merge_request.summary,
            description=description,
            pixmaps=pixmaps(merge_request.look),
            menu=[
                MenuEntry(merge_request.summary, opening),
                MenuEntry(merge_request.title),
                MenuEntry(merge_request.details),
                SEPARATOR,
                MenuEntry("Open in browser", opening),
                MenuEntry("Check now", self.check_now),
            ] + _not_updated_entries(view),
            on_activate=lambda: self.desktop.notify(merge_request.summary, description),
        )

    def _only_not_updated(self, view: BoardView) -> dict[str, IconContent]:
        if not view.not_updated:
            return {}
        reasons = "\n".join(view.not_updated)
        return {"not updated": IconContent(
            title=view.not_updated_summary,
            description=reasons,
            pixmaps=pixmaps(view.not_updated_look),
            menu=[MenuEntry("Check now", self.check_now)] + _not_updated_entries(view),
            on_activate=lambda: self.desktop.notify(view.not_updated_summary, reasons),
        )}


def _not_updated_entries(view: BoardView) -> list[MenuEntry]:
    return [SEPARATOR, *(MenuEntry(f"Not updated: {reason}") for reason in view.not_updated)] if view.not_updated else []
