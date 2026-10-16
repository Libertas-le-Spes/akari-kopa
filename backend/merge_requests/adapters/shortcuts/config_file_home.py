from merge_requests.adapters.shortcuts.config_lines import ConfigLines
from merge_requests.adapters.shortcuts.environment import Environment


class ConfigFileHome:
    name: str
    desktops: set[str]

    def __init__(self, environment: Environment, lines: ConfigLines, line: str, marker: str):
        self.environment = environment
        self.lines = lines
        self.line = line
        self.marker = marker

    def here(self) -> bool:
        return self.environment.is_one_of(self.desktops) and self.lines.exists()

    def has_it(self) -> bool:
        return self.lines.has(self.marker)

    def add(self) -> None:
        self.lines.add(self.line)
        self.applied()

    def remove(self) -> None:
        self.lines.remove(self.marker)
        self.applied()

    def applied(self) -> None:
        return None
