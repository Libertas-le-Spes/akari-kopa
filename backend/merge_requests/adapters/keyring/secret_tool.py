from merge_requests.adapters.transport.command_line import CommandLine


class SecretTool:
    def __init__(self, command_line: CommandLine):
        self.command_line = command_line

    def lookup(self, attribute: str, value: str) -> str:
        if not self.command_line.installed("secret-tool"):
            return ""
        return self.command_line.everything_said("secret-tool", "lookup", attribute, value).strip()
