from merge_requests.adapters.transport.command_line import CommandLine


class XdgBrowser:
    def __init__(self, command_line: CommandLine):
        self.command_line = command_line

    def open(self, url: str) -> None:
        self.command_line.start("xdg-open", url)
