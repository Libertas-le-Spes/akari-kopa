from merge_requests.adapters.shortcuts.config_file_home import ConfigFileHome
from merge_requests.adapters.shortcuts.config_lines import ConfigLines
from merge_requests.adapters.shortcuts.environment import Environment
from merge_requests.adapters.transport.command_line import CommandLine


class Sway(ConfigFileHome):
    name = "Sway"
    desktops = {"sway"}

    def __init__(self, environment: Environment, command_line: CommandLine, command: str):
        super().__init__(environment, ConfigLines(environment.config_home / "sway" / "config"), f"bindsym Mod4+Ctrl+m exec {command}", command)
        self.command_line = command_line

    def applied(self) -> None:
        self.command_line.answer("swaymsg", "reload")
