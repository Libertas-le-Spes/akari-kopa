import os
import secrets
import stat

from akari_kopa.adapters.storage.folder_check import FolderRefused, opened_private_folder

PRIVATE_FILE = 0o600
NEW_FILE = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
EXISTING_FILE = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC


class PrivateFolder:
    def __init__(self, path: str):
        self.path = path

    def read(self, name: str) -> str:
        folder = opened_private_folder(self.path)
        try:
            return _read_own_file(folder, name)
        finally:
            os.close(folder)

    def write(self, name: str, text: str) -> None:
        folder = opened_private_folder(self.path)
        try:
            _write_whole(folder, name, text)
        finally:
            os.close(folder)


def _read_own_file(folder: int, name: str) -> str:
    file = os.open(name, EXISTING_FILE, dir_fd=folder)
    try:
        _refuse_unless_own_file(file, name)
    except FolderRefused:
        os.close(file)
        raise
    with os.fdopen(file, encoding="utf-8") as opened:
        return opened.read()


def _refuse_unless_own_file(file: int, name: str) -> None:
    found = os.fstat(file)
    if not stat.S_ISREG(found.st_mode) or found.st_uid != os.getuid():
        raise FolderRefused(f"{name} is not a file of this account's own")


def _write_whole(folder: int, name: str, text: str) -> None:
    writing = f".{name}.{secrets.token_hex(8)}.writing"
    file = os.open(writing, NEW_FILE, PRIVATE_FILE, dir_fd=folder)
    try:
        with os.fdopen(file, "w", encoding="utf-8") as opened:
            opened.write(text)
            opened.flush()
            os.fsync(opened.fileno())
        os.replace(writing, name, src_dir_fd=folder, dst_dir_fd=folder)
    except BaseException:
        os.unlink(writing, dir_fd=folder)
        raise
