from akari_kopa.adapters.transport.command_line import CommandLine

AZURE_DEVOPS = "499b84ac-1321-427f-aa17-267ca6975798"


class Az:
    def __init__(self, command_line: CommandLine):
        self.command_line = command_line

    def installed(self) -> bool:
        return self.command_line.installed("az")

    def access_token(self) -> str | None:
        return self.command_line.answer(
            "az", "account", "get-access-token", "--resource", AZURE_DEVOPS, "--query", "accessToken", "--output", "tsv")
