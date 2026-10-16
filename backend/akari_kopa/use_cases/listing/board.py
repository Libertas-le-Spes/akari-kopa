from dataclasses import dataclass

from akari_kopa.attention.merge_request.merge_request import MergeRequest


@dataclass(frozen=True)
class NotUpdated:
    service: str
    reason: str


@dataclass(frozen=True)
class Board:
    merge_requests: list[MergeRequest]
    not_updated: list[NotUpdated]
