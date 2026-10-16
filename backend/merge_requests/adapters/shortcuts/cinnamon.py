from merge_requests.adapters.shortcuts.environment import Environment
from merge_requests.adapters.shortcuts.gsettings import GSettings

LIST_SCHEMA = "org.cinnamon.desktop.keybindings"
LIST_KEY = "custom-list"
ID = "merge-requests"
ENTRY = f"org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/{ID}/"


class Cinnamon:
    name = "Cinnamon"
    desktops = {"x-cinnamon", "cinnamon"}

    def __init__(self, environment: Environment, settings: GSettings, command: str):
        self.environment = environment
        self.settings = settings
        self.command = command

    def here(self) -> bool:
        return self.environment.is_one_of(self.desktops) and self.settings.installed()

    def has_it(self) -> bool:
        return ID in self.settings.strings(LIST_SCHEMA, LIST_KEY)

    def add(self) -> None:
        self.settings.set_text(ENTRY, "name", "Merge requests")
        self.settings.set_text(ENTRY, "command", self.command)
        self.settings.set_strings(ENTRY, "binding", ["<Super><Control>m"])
        self.settings.set_strings(LIST_SCHEMA, LIST_KEY, [*self.settings.strings(LIST_SCHEMA, LIST_KEY), ID])

    def remove(self) -> None:
        self.settings.set_strings(LIST_SCHEMA, LIST_KEY, [each for each in self.settings.strings(LIST_SCHEMA, LIST_KEY) if each != ID])
        for key in ("name", "command", "binding"):
            self.settings.reset(ENTRY, key)
