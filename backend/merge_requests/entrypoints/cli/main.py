import json
import sys

from merge_requests.entrypoints.choose.choose import Choose
from merge_requests.entrypoints.tray.tray import Tray
from merge_requests.presenters.board.board_view import board_view
from merge_requests.use_cases.shortcut.shortcut_setup import NoShortcutHome
from merge_requests.wiring import App, desktop, open_app


def board(app: App) -> None:
    json.dump(board_view(app.listing.board()).as_json(), sys.stdout)
    print()


def tray(app: App) -> None:
    Tray(app.listing, desktop()).run()


def choose(app: App) -> None:
    _say(Choose(app.listing, app.chooser, app.browser).run())


def shortcut(app: App) -> None:
    _say(app.shortcut.add())


def remove_shortcut(app: App) -> None:
    _say(app.shortcut.remove())


def _say(message: str) -> None:
    if message:
        print(message)


COMMANDS = {"board": board, "tray": tray, "choose": choose, "shortcut": shortcut, "remove-shortcut": remove_shortcut}


def main(arguments: list[str]) -> int:
    command = COMMANDS.get(arguments[0] if arguments else "board")
    if command is None:
        print(f"merge-requests: say one of {', '.join(COMMANDS)}", file=sys.stderr)
        return 2
    try:
        command(open_app())
    except NoShortcutHome as error:
        print(f"merge-requests: {error}", file=sys.stderr)
        return 1
    return 0
