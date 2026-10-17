from dataclasses import dataclass, field

from akari_kopa.attention.merge_request.merge_request import MergeRequest


@dataclass(frozen=True)
class NotUpdated:
    service: str
    reason: str


@dataclass(frozen=True)
class Board:
    merge_requests: list[MergeRequest]
    not_updated: list[NotUpdated]
    headings: dict[str, str] = field(default_factory=dict)

    def heading_of(self, service: str) -> str:
        return self.headings.get(service, service)
