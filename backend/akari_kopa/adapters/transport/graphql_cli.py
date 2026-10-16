from akari_kopa.adapters.transport.command_line import CommandLine


class GraphQlCli:
    def __init__(self, command_line: CommandLine, tool: str):
        self.command_line = command_line
        self.tool = tool

    def installed(self) -> bool:
        return self.command_line.installed(self.tool)

    def hosts(self) -> list[str]:
        said = self.command_line.everything_said(self.tool, "auth", "status")
        named = [line.strip() for line in said.splitlines() if line and not line[0].isspace()]
        return [host for host in named if self.command_line.succeeds(self.tool, "auth", "status", "--hostname", host)]

    def ask(self, host: str, query: str, **variables: str) -> dict:
        fields = [argument for name, value in variables.items() for argument in ("-f", f"{name}={value}")]
        return self.command_line.json(self.tool, "api", "--hostname", host, "graphql", "-f", f"query={query}", *fields)
