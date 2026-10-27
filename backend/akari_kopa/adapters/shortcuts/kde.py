from akari_kopa.adapters.shortcuts.environment import Environment
from akari_kopa.adapters.shortcuts.text_files import TextFiles
from akari_kopa.adapters.transport.command_line import CommandLine

LAUNCHER = "akari-kopa-choose.desktop"
KEYS = "Meta+Ctrl+M"
CONFIG_TOOLS = ("kwriteconfig6", "kwriteconfig5")


class Kde:
    name = "KDE Plasma"
    desktops = {"kde"}

    def __init__(self, environment: Environment, command_line: CommandLine, files: TextFiles, command: str):
        self.environment = environment
        self.command_line = command_line
        self.files = files
        self.command = command
        self.launcher = environment.data_home / "applications" / LAUNCHER

    def here(self) -> bool:
        return self.environment.is_one_of(self.desktops) and self._config_tool() is not None

    def has_it(self) -> bool:
        return self.files.exists(self.launcher)

    def add(self) -> None:
        entry = f"[Desktop Entry]\nType=Application\nName=Akari Kopa\nExec={self.command}\nNoDisplay=true\nX-KDE-Shortcuts={KEYS}\n"
        self.files.write_whole(self.launcher, entry, was=None)
        self._shortcut(KEYS)

    def remove(self) -> None:
        self._shortcut("none")
        self.files.remove(self.launcher)

    def _shortcut(self, keys: str) -> None:
        self.command_line.text(self._config_tool(), "--file", "kglobalshortcutsrc", "--group", "services", "--group", LAUNCHER,
                               "--key", "_launch", keys)
        self.command_line.answer("kbuildsycoca6")

    def _config_tool(self) -> str | None:
        for tool in CONFIG_TOOLS:
            if self.command_line.installed(tool):
                return tool
        return None
