import string

from akari_kopa.use_cases.shortcut.ports import ShortcutRefused

SAFE_CHARACTERS = frozenset(string.ascii_letters + string.digits + "/._-")


def check_install_path(path: str) -> None:
    for character in path:
        if character not in SAFE_CHARACTERS:
            raise ShortcutRefused(
                f"Akari Kopa is installed in {path!r}; a shortcut is only set up from a folder whose name has"
                " letters, digits, '/', '.', '_' and '-'. Move it to such a folder and try again.")
