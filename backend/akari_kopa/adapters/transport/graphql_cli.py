import json

from akari_kopa.adapters.transport.command_line import CommandLine
from akari_kopa.use_cases.listing.ports import ServiceError

JSON_BODY = "Content-Type: application/json"


class GraphQlCli:
    def __init__(self, command_line: CommandLine, tool: str, endpoint: str):
        self.command_line = command_line
        self.tool = tool
        self.endpoint = endpoint

    def installed(self) -> bool:
        return self.command_line.installed(self.tool)

    def hosts(self) -> list[str]:
        said = self.command_line.everything_said(self.tool, "auth", "status")
        hosts = []
        for host in _named_hosts(said):
            if self.command_line.succeeds(self.tool, "auth", "status", "--hostname", host):
                hosts.append(host)
        return hosts

    def ask(self, host: str, query: str, variables: dict[str, str]) -> dict:
        body = json.dumps({"query": query, "variables": variables})
        answer = self.command_line.json(self.tool, "api", "--hostname", host, "--method", "POST", "--header", JSON_BODY,
                                        self.endpoint, "--input", "-", given=body)
        _refuse_errors(self.tool, answer)
        return answer


def _refuse_errors(tool: str, answer: dict) -> None:
    errors = answer.get("errors")
    if errors:
        raise ServiceError(f"{tool}: {_first_message(errors)}")


def _first_message(errors: list[dict]) -> str:
    first = errors[0]
    if "message" in first:
        return first["message"]
    return "the query was refused"


def _named_hosts(said: str) -> list[str]:
    named = []
    for line in said.splitlines():
        if line and not line[0].isspace():
            named.append(line.strip())
    return named
