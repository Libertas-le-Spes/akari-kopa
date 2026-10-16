from akari_kopa.adapters.transport.command_line import CommandLine
from akari_kopa.use_cases.choosing.ports import Option


class Zenity:
    name = "zenity"

    def __init__(self, command_line: CommandLine):
        self.command_line = command_line

    def installed(self) -> bool:
        return self.command_line.installed("zenity")

    def choose(self, title: str, question: str, options: list[Option]) -> str | None:
        rows = [cell for option in options for cell in (option.key, option.label, option.detail)]
        return self.command_line.answer(
            "zenity", "--list", f"--title={title}", f"--text={question}", "--width=760", "--height=420",
            "--column=key", "--column=Merge request", "--column=Details", "--hide-column=1", "--print-column=1", *rows,
        ) or None
