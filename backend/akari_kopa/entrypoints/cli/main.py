import json
import sys

from akari_kopa.entrypoints.choose.choose import Choose
from akari_kopa.entrypoints.tray.tray import Tray
from akari_kopa.presenters.board.board_view import board_view
from akari_kopa.use_cases.shortcut.ports import ShortcutRefused
from akari_kopa.wiring import App, desktop, open_app


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


def _asked(arguments: list[str]) -> str:
    if not arguments:
        return "board"
    return arguments[0]


def main(arguments: list[str]) -> int:
    command = COMMANDS.get(_asked(arguments))
    if command is None:
        print(f"akari-kopa: say one of {', '.join(COMMANDS)}", file=sys.stderr)
        return 2
    try:
        command(open_app())
    except ShortcutRefused as error:
        print(f"akari-kopa: {error}", file=sys.stderr)
        return 1
    return 0
