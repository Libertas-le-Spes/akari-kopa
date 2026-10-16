from merge_requests.adapters.shortcuts.environment import Environment
from merge_requests.adapters.shortcuts.gsettings import GSettings

LIST_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
LIST_KEY = "custom-keybindings"
PATH = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/merge-requests/"
ENTRY = f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{PATH}"


class Gnome:
    name = "GNOME"
    desktops = {"gnome", "budgie", "unity"}

    def __init__(self, environment: Environment, settings: GSettings, command: str):
        self.environment = environment
        self.settings = settings
        self.command = command

    def here(self) -> bool:
        return self.environment.is_one_of(self.desktops) and self.settings.installed()

    def has_it(self) -> bool:
        return PATH in self.settings.strings(LIST_SCHEMA, LIST_KEY)

    def add(self) -> None:
        self.settings.set_text(ENTRY, "name", "Merge requests")
        self.settings.set_text(ENTRY, "command", self.command)
        self.settings.set_text(ENTRY, "binding", "<Super><Control>m")
        self.settings.set_strings(LIST_SCHEMA, LIST_KEY, [*self.settings.strings(LIST_SCHEMA, LIST_KEY), PATH])

    def remove(self) -> None:
        self.settings.set_strings(LIST_SCHEMA, LIST_KEY, [path for path in self.settings.strings(LIST_SCHEMA, LIST_KEY) if path != PATH])
        for key in ("name", "command", "binding"):
            self.settings.reset(ENTRY, key)
