from akari_kopa.adapters.shortcuts.config_file_home import ConfigFileHome
from akari_kopa.adapters.shortcuts.config_lines import ConfigLines
from akari_kopa.adapters.shortcuts.environment import Environment
from akari_kopa.adapters.shortcuts.text_files import TextFiles
from akari_kopa.adapters.transport.command_line import CommandLine

POPUP = "omarchy-shell kayu.akari-kopa toggle"


class Omarchy(ConfigFileHome):
    name = "Omarchy"
    desktops = {"hyprland"}

    def __init__(self, environment: Environment, command_line: CommandLine, files: TextFiles, command: str):
        line = f'o.bind("SUPER + CTRL + M", "Akari Kopa", "{POPUP}")'
        super().__init__(environment, ConfigLines(environment.config_home / "hypr" / "bindings.lua", files), line, POPUP)
        self.command_line = command_line

    def here(self) -> bool:
        return super().here() and self.command_line.installed("omarchy-shell")

    def applied(self) -> None:
        self.command_line.answer("hyprctl", "reload")


class HyprlandLua(ConfigFileHome):
    name = "Hyprland"
    desktops = {"hyprland"}

    def __init__(self, environment: Environment, command_line: CommandLine, files: TextFiles, command: str):
        line = f'hl.bind("SUPER + CTRL + M", hl.dsp.exec_cmd("{command}"), {{ description = "Akari Kopa" }})'
        super().__init__(environment, ConfigLines(environment.config_home / "hypr" / "hyprland.lua", files), line, command)
        self.command_line = command_line

    def applied(self) -> None:
        self.command_line.answer("hyprctl", "reload")


class HyprlandConf(ConfigFileHome):
    name = "Hyprland"
    desktops = {"hyprland"}

    def __init__(self, environment: Environment, command_line: CommandLine, files: TextFiles, command: str):
        super().__init__(environment, ConfigLines(environment.config_home / "hypr" / "hyprland.conf", files), f"bind = SUPER CTRL, M, exec, {command}", command)
        self.command_line = command_line

    def applied(self) -> None:
        self.command_line.answer("hyprctl", "reload")
