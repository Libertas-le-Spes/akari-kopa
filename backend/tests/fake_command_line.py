from akari_kopa.use_cases.listing.ports import ServiceError


class FakeCommandLine:
    def __init__(self, tools: set[str], answers: dict[tuple, object] | None = None, said: dict[tuple, str] | None = None):
        self.tools = tools
        self.answers = _given_or_none(answers)
        self.said = _given_or_none(said)
        self.asked: list[tuple] = []
        self.given: list[str] = []

    def installed(self, tool: str) -> bool:
        return tool in self.tools

    def succeeds(self, *arguments: str) -> bool:
        return arguments in self.said or _asks_tea_api(arguments)

    def everything_said(self, *arguments: str) -> str:
        return self.said.get(arguments, "")

    def answer(self, *arguments: str) -> str | None:
        self.asked.append(arguments)
        return self.said.get(arguments)

    def text(self, *arguments: str) -> str:
        self.asked.append(arguments)
        self._settle(arguments)
        return ""

    def start(self, *arguments: str) -> None:
        self.asked.append(arguments)

    def _settle(self, arguments: tuple) -> None:
        if arguments[:2] == ("gsettings", "set"):
            self.said[("gsettings", "get", arguments[2], arguments[3])] = arguments[4]
        if arguments[:2] == ("gsettings", "reset"):
            self.said.pop(("gsettings", "get", arguments[2], arguments[3]), None)

    def chosen(self, given: str, *arguments: str) -> str | None:
        self.given.append(given)
        self.asked.append(arguments)
        return self.said.get(arguments)

    def json(self, *arguments: str, given: str = ""):
        self.asked.append(arguments)
        self.given.append(given)
        for key, answer in self.answers.items():
            if _all_present(key, arguments, given):
                return answer
        raise ServiceError(f"nothing prepared for {arguments}")


def _all_present(key: tuple, arguments: tuple, given: str) -> bool:
    for part in key:
        if part not in arguments and part not in given:
            return False
    return True


def _given_or_none(prepared: dict | None) -> dict:
    if prepared is None:
        return {}
    return prepared


def _asks_tea_api(arguments: tuple) -> bool:
    return len(arguments) >= 2 and arguments[0] == "tea" and arguments[1] == "api"
