from dataclasses import dataclass
from urllib.parse import urlsplit

from akari_kopa.adapters.transport.command_line import CommandLine
from akari_kopa.use_cases.listing.ports import ServiceError


@dataclass(frozen=True)
class TeaLogin:
    name: str
    host: str


class Tea:
    def __init__(self, command_line: CommandLine):
        self.command_line = command_line

    def installed(self) -> bool:
        return self.command_line.installed("tea")

    def logins(self) -> list[TeaLogin]:
        if not self.command_line.succeeds("tea", "api", "--help"):
            raise ServiceError("tea is too old: version 0.12 or newer is needed")
        logins = []
        for login in self.command_line.json("tea", "logins", "list", "--output", "json"):
            logins.append(TeaLogin(login["name"], urlsplit(login["url"]).netloc))
        return logins

    def get(self, login: TeaLogin, path: str):
        return self.command_line.json("tea", "api", "--login", login.name, path)
