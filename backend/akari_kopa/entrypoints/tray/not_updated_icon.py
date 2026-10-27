from functools import partial
from typing import Callable

from akari_kopa.presenters.board.views import BoardView
from akari_kopa.presenters.orb.pixmap import pixmaps
from akari_kopa.use_cases.desktop.ports import SEPARATOR, Desktop, IconContent, MenuEntry


def only_not_updated(view: BoardView, desktop: Desktop, check_now: Callable[[], None]) -> dict[str, IconContent]:
    if not view.not_updated:
        return {}
    reasons = "\n".join(view.not_updated)
    return {"not updated": IconContent(
        title=view.not_updated_summary,
        description=reasons,
        pixmaps=pixmaps(view.not_updated_look),
        menu=[MenuEntry("Check now", check_now)] + not_updated_entries(view),
        on_activate=partial(desktop.notify, view.not_updated_summary, reasons),
    )}


def not_updated_entries(view: BoardView) -> list[MenuEntry]:
    if not view.not_updated:
        return []
    entries = [SEPARATOR]
    for reason in view.not_updated:
        entries.append(MenuEntry(f"Not updated: {reason}"))
    return entries
