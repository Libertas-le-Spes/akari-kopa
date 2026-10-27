from dataclasses import asdict, dataclass

from akari_kopa.attention.merge_request.web_address import RefusedAddress, WebAddress
from akari_kopa.presenters.orb.look import Look


@dataclass(frozen=True)
class MergeRequestView:
    key: str
    summary: str
    title: str
    details: str
    address: WebAddress | RefusedAddress
    service: str
    look: Look


@dataclass(frozen=True)
class ServiceView:
    heading: str
    merge_requests: list[MergeRequestView]


@dataclass(frozen=True)
class GroupView:
    heading: str
    services: list[ServiceView]


@dataclass(frozen=True)
class BoardView:
    groups: list[GroupView]
    not_updated: list[str]
    not_updated_summary: str
    not_updated_look: Look

    def merge_requests(self) -> list[MergeRequestView]:
        found = []
        for group in self.groups:
            for service in group.services:
                found += service.merge_requests
        return found

    def find(self, key: str | None) -> MergeRequestView | None:
        for merge_request in self.merge_requests():
            if merge_request.key == key:
                return merge_request
        return None

    def as_json(self) -> dict:
        return asdict(self)
