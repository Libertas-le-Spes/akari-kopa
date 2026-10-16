from akari_kopa.use_cases.shortcut.ports import KEYS, ShortcutHome


class NoShortcutHome(Exception):
    pass


class ShortcutSetup:
    def __init__(self, homes: list[ShortcutHome]):
        self.homes = homes

    def add(self) -> str:
        home = self._this_desktop()
        if home.has_it():
            return f"{KEYS} already opens your merge requests ({home.name})."
        home.add()
        return f"{KEYS} now opens your merge requests ({home.name})."

    def remove(self) -> str:
        present = [home for home in self.homes if home.here() and home.has_it()]
        for home in present:
            home.remove()
        return f"Removed the shortcut ({', '.join(home.name for home in present)})." if present else "There was no shortcut to remove."

    def _this_desktop(self) -> ShortcutHome:
        home = next((home for home in self.homes if home.here()), None)
        if home is None:
            supported = ", ".join(dict.fromkeys(home.name for home in self.homes))
            raise NoShortcutHome(f"This desktop is not one akari-kopa can set a shortcut on yet ({supported}).")
        return home
