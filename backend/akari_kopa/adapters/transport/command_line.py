import json
import shutil
import subprocess

from akari_kopa.use_cases.listing.ports import ServiceError

REASON_LENGTH = 160
TIMEOUT_SECONDS = 60


class CommandLine:
    def installed(self, tool: str) -> bool:
        return shutil.which(tool) is not None

    def answer(self, *arguments: str) -> str | None:
        if not self.installed(arguments[0]):
            return None
        finished = self._run(arguments, "")
        if finished.returncode != 0:
            return None
        return finished.stdout.strip()

    def chosen(self, given: str, *arguments: str) -> str | None:
        finished = subprocess.run(arguments, input=given, capture_output=True, text=True)
        if finished.returncode != 0:
            return None
        return finished.stdout.strip()

    def start(self, *arguments: str) -> None:
        subprocess.Popen(arguments, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

    def succeeds(self, *arguments: str) -> bool:
        return self._run(arguments, "").returncode == 0

    def text(self, *arguments: str, given: str = "") -> str:
        if not self.installed(arguments[0]):
            raise ServiceError(f"{arguments[0]} is not installed")
        finished = self._run(arguments, given)
        if finished.returncode != 0:
            raise ServiceError(_reason(finished.stderr, arguments[0]))
        return finished.stdout

    def everything_said(self, *arguments: str) -> str:
        return self._run(arguments, "", together=True).stdout

    def json(self, *arguments: str, given: str = ""):
        try:
            return json.loads(self.text(*arguments, given=given))
        except ValueError as error:
            raise ServiceError(f"{arguments[0]} gave an answer that is not JSON: {error}") from error

    def _run(self, arguments: tuple, given: str, together: bool = False) -> subprocess.CompletedProcess:
        errors = subprocess.PIPE
        if together:
            errors = subprocess.STDOUT
        try:
            return subprocess.run(arguments, input=given, stdout=subprocess.PIPE, stderr=errors, text=True, timeout=TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as error:
            raise ServiceError(f"{arguments[0]} did not answer within {TIMEOUT_SECONDS} seconds") from error


def _reason(errors: str, tool: str) -> str:
    lines = []
    for line in errors.splitlines():
        if line.strip():
            lines.append(line)
    if not lines:
        return f"{tool} failed"
    return lines[-1][:REASON_LENGTH]
