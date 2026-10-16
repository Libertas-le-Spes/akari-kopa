from dataclasses import asdict, dataclass

from merge_requests.attention.merge_request.merge_request import MergeRequest
from merge_requests.attention.merge_request.role import ROLES
from merge_requests.presenters.orb.look import NOT_UPDATED, Look, look_of, word_of
from merge_requests.use_cases.listing.board import Board


@dataclass(frozen=True)
class MergeRequestView:
    key: str
    summary: str
    title: str
    details: str
    url: str
    look: Look


@dataclass(frozen=True)
class GroupView:
    heading: str
    merge_requests: list[MergeRequestView]


@dataclass(frozen=True)
class BoardView:
    groups: list[GroupView]
    not_updated: list[str]
    not_updated_summary: str
    not_updated_look: Look

    def merge_requests(self) -> list[MergeRequestView]:
        return [merge_request for group in self.groups for merge_request in group.merge_requests]

    def as_json(self) -> dict:
        return asdict(self)


def board_view(board: Board) -> BoardView:
    faded = bool(board.not_updated)
    groups = [GroupView(role.heading, [_view(mr, faded) for mr in board.merge_requests if mr.role == role]) for role in ROLES.values()]
    return BoardView(
        [group for group in groups if group.merge_requests],
        [f"{failure.service}: {failure.reason}" for failure in board.not_updated],
        "Not updated: " + ", ".join(failure.service for failure in board.not_updated) if faded else "",
        NOT_UPDATED,
    )


def _view(merge_request: MergeRequest, faded: bool) -> MergeRequestView:
    return MergeRequestView(
        key=f"{merge_request.service} {merge_request.url}",
        summary=f"{merge_request.reference} · {merge_request.author}",
        title=merge_request.title,
        details=f"{merge_request.project} · {merge_request.role.word} · {word_of(merge_request)}",
        url=merge_request.url,
        look=look_of(merge_request, faded),
    )
