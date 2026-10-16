import ast

from merge_requests.adapters.transport.command_line import CommandLine


class GSettings:
    def __init__(self, command_line: CommandLine):
        self.command_line = command_line

    def installed(self) -> bool:
        return self.command_line.installed("gsettings")

    def strings(self, schema: str, key: str) -> list[str]:
        said = self.command_line.answer("gsettings", "get", schema, key) or "[]"
        return list(ast.literal_eval(said.removeprefix("@as ")))

    def text(self, schema: str, key: str) -> str:
        said = self.command_line.answer("gsettings", "get", schema, key) or "''"
        return ast.literal_eval(said)

    def set_strings(self, schema: str, key: str, values: list[str]) -> None:
        self.command_line.text("gsettings", "set", schema, key, str(values))

    def set_text(self, schema: str, key: str, value: str) -> None:
        self.command_line.text("gsettings", "set", schema, key, repr(value))

    def reset(self, schema: str, key: str) -> None:
        self.command_line.text("gsettings", "reset", schema, key)
