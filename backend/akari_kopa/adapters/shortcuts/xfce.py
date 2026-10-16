from akari_kopa.adapters.shortcuts.environment import Environment
from akari_kopa.adapters.transport.command_line import CommandLine

CHANNEL = "xfce4-keyboard-shortcuts"
PROPERTY = "/commands/custom/<Super><Primary>m"


class Xfce:
    name = "Xfce"
    desktops = {"xfce"}

    def __init__(self, environment: Environment, command_line: CommandLine, command: str):
        self.environment = environment
        self.command_line = command_line
        self.command = command

    def here(self) -> bool:
        return self.environment.is_one_of(self.desktops) and self.command_line.installed("xfconf-query")

    def has_it(self) -> bool:
        return self.command_line.answer("xfconf-query", "-c", CHANNEL, "-p", PROPERTY) == self.command

    def add(self) -> None:
        self.command_line.text("xfconf-query", "-c", CHANNEL, "-p", PROPERTY, "-n", "-t", "string", "-s", self.command)

    def remove(self) -> None:
        self.command_line.text("xfconf-query", "-c", CHANNEL, "-p", PROPERTY, "-r")
