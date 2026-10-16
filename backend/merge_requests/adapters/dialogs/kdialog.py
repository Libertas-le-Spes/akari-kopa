from merge_requests.adapters.transport.command_line import CommandLine
from merge_requests.use_cases.choosing.ports import Option


class Kdialog:
    name = "kdialog"

    def __init__(self, command_line: CommandLine):
        self.command_line = command_line

    def installed(self) -> bool:
        return self.command_line.installed("kdialog")

    def choose(self, title: str, question: str, options: list[Option]) -> str | None:
        items = [cell for option in options for cell in (option.key, f"{option.label}  ·  {option.detail}")]
        return self.command_line.answer("kdialog", "--title", title, "--menu", question, *items) or None
