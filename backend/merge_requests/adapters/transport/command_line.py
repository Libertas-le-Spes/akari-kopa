import json
import shutil
import subprocess

from merge_requests.use_cases.listing.ports import ServiceError

REASON_LENGTH = 160


class CommandLine:
    def installed(self, tool: str) -> bool:
        return shutil.which(tool) is not None

    def answer(self, *arguments: str) -> str | None:
        if not self.installed(arguments[0]):
            return None
        finished = subprocess.run(arguments, capture_output=True, text=True)
        return finished.stdout.strip() if finished.returncode == 0 else None

    def start(self, *arguments: str) -> None:
        subprocess.Popen(arguments, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

    def succeeds(self, *arguments: str) -> bool:
        return subprocess.run(arguments, capture_output=True).returncode == 0

    def text(self, *arguments: str) -> str:
        if not self.installed(arguments[0]):
            raise ServiceError(f"{arguments[0]} is not installed")
        finished = subprocess.run(arguments, capture_output=True, text=True)
        if finished.returncode != 0:
            raise ServiceError(_reason(finished.stderr) or f"{arguments[0]} failed")
        return finished.stdout

    def everything_said(self, *arguments: str) -> str:
        finished = subprocess.run(arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return finished.stdout

    def json(self, *arguments: str):
        try:
            return json.loads(self.text(*arguments))
        except ValueError as error:
            raise ServiceError(f"{arguments[0]} gave an answer that is not JSON: {error}") from error


def _reason(errors: str) -> str:
    lines = [line for line in errors.splitlines() if line.strip()]
    return lines[-1][:REASON_LENGTH] if lines else ""
