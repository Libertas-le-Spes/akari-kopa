import json
import sys

from merge_requests.entrypoints.tray.tray import Tray
from merge_requests.presenters.board.board_view import board_view
from merge_requests.wiring import App, desktop, open_app


def board(app: App) -> None:
    json.dump(board_view(app.listing.board()).as_json(), sys.stdout)
    print()


def tray(app: App) -> None:
    Tray(app.listing, desktop()).run()


COMMANDS = {"board": board, "tray": tray}


def main(arguments: list[str]) -> int:
    command = COMMANDS.get(arguments[0] if arguments else "board")
    if command is None:
        print(f"merge-requests: say one of {', '.join(COMMANDS)}", file=sys.stderr)
        return 2
    command(open_app())
    return 0
