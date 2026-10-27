import json
import sys
from dataclasses import dataclass
from datetime import datetime

from akari_kopa.adapters.storage.merge_request_codec import decoded, encoded
from akari_kopa.adapters.storage.private_folder import PrivateFolder
from akari_kopa.attention.merge_request.merge_request import MergeRequest


@dataclass(frozen=True)
class StoredAnswer:
    merge_requests: list[MergeRequest]
    given: datetime


class AnswerFolder:
    def __init__(self, folder: PrivateFolder):
        self.folder = folder

    def last(self, service: str) -> StoredAnswer | None:
        try:
            raw = json.loads(self.folder.read(f"{service}.json"))
            return StoredAnswer(_decoded_all(raw["mergeRequests"]), datetime.fromisoformat(raw["given"]))
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def keep(self, service: str, merge_requests: list[MergeRequest], given: datetime) -> None:
        text = json.dumps({"given": given.isoformat(), "mergeRequests": _encoded_all(merge_requests)})
        try:
            self.folder.write(f"{service}.json", text)
        except OSError as problem:
            print(f"akari-kopa: kept nothing for {service}: {problem}", file=sys.stderr)


def _decoded_all(raw: list[dict]) -> list[MergeRequest]:
    found = []
    for each in raw:
        found.append(decoded(each))
    return found


def _encoded_all(merge_requests: list[MergeRequest]) -> list[dict]:
    found = []
    for merge_request in merge_requests:
        found.append(encoded(merge_request))
    return found
