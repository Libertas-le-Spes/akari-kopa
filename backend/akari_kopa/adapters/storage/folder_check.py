import os
import stat


class FolderRefused(OSError):
    pass


PRIVATE = 0o700
OPEN_FOLDER = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def opened_private_folder(path: str) -> int:
    os.makedirs(path, mode=PRIVATE, exist_ok=True)
    try:
        folder = os.open(path, OPEN_FOLDER)
    except OSError as error:
        raise FolderRefused(f"{path} is not a folder of its own: {error.strerror}") from error
    try:
        _make_private(folder, path)
    except FolderRefused:
        os.close(folder)
        raise
    return folder


def _make_private(folder: int, path: str) -> None:
    found = os.fstat(folder)
    if found.st_uid != os.getuid():
        raise FolderRefused(f"{path} belongs to another account")
    if stat.S_IMODE(found.st_mode) != PRIVATE:
        os.fchmod(folder, PRIVATE)
