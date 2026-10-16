from akari_kopa.adapters.shortcuts.environment import Environment
from akari_kopa.adapters.transport.command_line import CommandLine

LAUNCHER = "akari-kopa-choose.desktop"
KEYS = "Meta+Ctrl+M"


class Kde:
    name = "KDE Plasma"
    desktops = {"kde"}

    def __init__(self, environment: Environment, command_line: CommandLine, command: str):
        self.environment = environment
        self.command_line = command_line
        self.command = command
        self.launcher = environment.data_home / "applications" / LAUNCHER

    def here(self) -> bool:
        return self.environment.is_one_of(self.desktops) and self._config_tool() is not None

    def has_it(self) -> bool:
        return self.launcher.is_file()

    def add(self) -> None:
        self.launcher.parent.mkdir(parents=True, exist_ok=True)
        self.launcher.write_text(
            f"[Desktop Entry]\nType=Application\nName=Akari Kopa\nExec={self.command}\nNoDisplay=true\nX-KDE-Shortcuts={KEYS}\n",
            encoding="utf-8",
        )
        self._shortcut(KEYS)

    def remove(self) -> None:
        self._shortcut("none")
        self.launcher.unlink(missing_ok=True)

    def _shortcut(self, keys: str) -> None:
        self.command_line.text(self._config_tool(), "--file", "kglobalshortcutsrc", "--group", "services", "--group", LAUNCHER,
                               "--key", "_launch", keys)
        self.command_line.answer("kbuildsycoca6")

    def _config_tool(self) -> str | None:
        return next((tool for tool in ("kwriteconfig6", "kwriteconfig5") if self.command_line.installed(tool)), None)
