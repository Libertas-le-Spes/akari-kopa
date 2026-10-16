import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from akari_kopa.adapters.storage.merge_request_codec import decoded, encoded
from akari_kopa.attention.merge_request.merge_request import MergeRequest


@dataclass(frozen=True)
class StoredAnswer:
    merge_requests: list[MergeRequest]
    given: datetime


class AnswerFolder:
    def __init__(self, folder: Path):
        self.folder = folder

    def last(self, service: str) -> StoredAnswer | None:
        try:
            raw = json.loads(self._file(service).read_text(encoding="utf-8"))
            return StoredAnswer([decoded(each) for each in raw["mergeRequests"]], datetime.fromisoformat(raw["given"]))
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def keep(self, service: str, merge_requests: list[MergeRequest], given: datetime) -> None:
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        written = self._file(service).with_suffix(".writing")
        written.write_text(json.dumps({"given": given.isoformat(), "mergeRequests": [encoded(each) for each in merge_requests]}), encoding="utf-8")
        written.chmod(0o600)
        os.replace(written, self._file(service))

    def _file(self, service: str) -> Path:
        return self.folder / f"{service}.json"
