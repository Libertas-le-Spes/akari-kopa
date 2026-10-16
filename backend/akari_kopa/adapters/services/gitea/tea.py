from akari_kopa.adapters.transport.command_line import CommandLine
from akari_kopa.use_cases.listing.ports import ServiceError


class Tea:
    def __init__(self, command_line: CommandLine):
        self.command_line = command_line

    def installed(self) -> bool:
        return self.command_line.installed("tea")

    def logins(self) -> list[str]:
        if not self.command_line.succeeds("tea", "api", "--help"):
            raise ServiceError("tea is too old: version 0.12 or newer is needed")
        return [login["name"] for login in self.command_line.json("tea", "logins", "list", "--output", "json")]

    def get(self, login: str, path: str):
        return self.command_line.json("tea", "api", "--login", login, path)
