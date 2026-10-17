from dataclasses import asdict, dataclass

from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import ROLES
from akari_kopa.presenters.orb.look import NOT_UPDATED, Look, look_of, word_of
from akari_kopa.use_cases.listing.board import Board


@dataclass(frozen=True)
class MergeRequestView:
    key: str
    summary: str
    title: str
    details: str
    url: str
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
        return [merge_request for group in self.groups for service in group.services for merge_request in service.merge_requests]

    def as_json(self) -> dict:
        return asdict(self)


def board_view(board: Board) -> BoardView:
    faded = bool(board.not_updated)
    groups = [GroupView(role.heading, _by_service([mr for mr in board.merge_requests if mr.role == role], board, faded)) for role in ROLES.values()]
    return BoardView(
        [group for group in groups if group.services],
        [f"{board.heading_of(failure.service)}: {failure.reason}" for failure in board.not_updated],
        "Not updated: " + ", ".join(board.heading_of(failure.service) for failure in board.not_updated) if faded else "",
        NOT_UPDATED,
    )


def _by_service(merge_requests: list[MergeRequest], board: Board, faded: bool) -> list[ServiceView]:
    services = dict.fromkeys(merge_request.service for merge_request in merge_requests)
    return [ServiceView(board.heading_of(service), [_view(mr, board, faded) for mr in merge_requests if mr.service == service]) for service in services]


def _view(merge_request: MergeRequest, board: Board, faded: bool) -> MergeRequestView:
    return MergeRequestView(
        key=f"{merge_request.service} {merge_request.url}",
        summary=f"{merge_request.reference} · {merge_request.author}",
        title=merge_request.title,
        details=f"{merge_request.project} · {merge_request.role.word} · {word_of(merge_request)}",
        url=merge_request.url,
        service=board.heading_of(merge_request.service),
        look=look_of(merge_request, faded),
    )
