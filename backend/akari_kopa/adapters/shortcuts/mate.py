from akari_kopa.adapters.shortcuts.environment import Environment
from akari_kopa.adapters.shortcuts.gsettings import GSettings

ENTRY = "org.mate.control-center.keybinding:/org/mate/desktop/keybindings/akari-kopa/"


class Mate:
    name = "MATE"
    desktops = {"mate"}

    def __init__(self, environment: Environment, settings: GSettings, command: str):
        self.environment = environment
        self.settings = settings
        self.command = command

    def here(self) -> bool:
        return self.environment.is_one_of(self.desktops) and self.settings.installed()

    def has_it(self) -> bool:
        return self.settings.text(ENTRY, "action") == self.command

    def add(self) -> None:
        self.settings.set_text(ENTRY, "name", "Akari Kopa")
        self.settings.set_text(ENTRY, "action", self.command)
        self.settings.set_text(ENTRY, "binding", "<Mod4><Control>m")

    def remove(self) -> None:
        for key in ("name", "action", "binding"):
            self.settings.reset(ENTRY, key)
