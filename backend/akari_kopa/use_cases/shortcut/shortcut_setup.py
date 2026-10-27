from akari_kopa.use_cases.shortcut.install_path import check_install_path
from akari_kopa.use_cases.shortcut.ports import KEYS, ShortcutHome, ShortcutRefused


class NoShortcutHome(ShortcutRefused):
    pass


class ShortcutSetup:
    def __init__(self, homes: list[ShortcutHome], install_path: str):
        self.homes = homes
        self.install_path = install_path

    def add(self) -> str:
        check_install_path(self.install_path)
        home = self._this_desktop()
        if home.has_it():
            return f"{KEYS} already opens your merge requests ({home.name})."
        home.add()
        return f"{KEYS} now opens your merge requests ({home.name})."

    def remove(self) -> str:
        present = []
        for home in self.homes:
            if home.here() and home.has_it():
                home.remove()
                present.append(home.name)
        if not present:
            return "There was no shortcut to remove."
        return f"Removed the shortcut ({', '.join(present)})."

    def _this_desktop(self) -> ShortcutHome:
        for home in self.homes:
            if home.here():
                return home
        supported = ", ".join(self._names())
        raise NoShortcutHome(f"This desktop is not one akari-kopa can set a shortcut on yet ({supported}).")

    def _names(self) -> list[str]:
        names = []
        for home in self.homes:
            if home.name not in names:
                names.append(home.name)
        return names
