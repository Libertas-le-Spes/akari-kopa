from akari_kopa.adapters.transport.command_line import CommandLine
from akari_kopa.attention.merge_request.web_address import WebAddress


class XdgBrowser:
    def __init__(self, command_line: CommandLine):
        self.command_line = command_line

    def open(self, address: WebAddress) -> None:
        self.command_line.start("xdg-open", address.text)
