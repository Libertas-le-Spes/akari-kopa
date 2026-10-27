from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import ROLES, Role
from akari_kopa.presenters.board.views import BoardView, GroupView, MergeRequestView, ServiceView
from akari_kopa.presenters.orb.look import NOT_UPDATED, look_of, word_of
from akari_kopa.use_cases.listing.board import Board


def board_view(board: Board) -> BoardView:
    faded = bool(board.not_updated)
    groups = []
    for role in ROLES.values():
        services = _by_service(_in_role(board, role), board, faded)
        if services:
            groups.append(GroupView(role.heading, services))
    return BoardView(groups, _reasons(board), _not_updated_summary(board), NOT_UPDATED)


def _in_role(board: Board, role: Role) -> list[MergeRequest]:
    found = []
    for merge_request in board.merge_requests:
        if merge_request.role == role:
            found.append(merge_request)
    return found


def _reasons(board: Board) -> list[str]:
    reasons = []
    for failure in board.not_updated:
        reasons.append(f"{board.heading_of(failure.service)}: {failure.reason}")
    return reasons


def _not_updated_summary(board: Board) -> str:
    if not board.not_updated:
        return ""
    headings = []
    for failure in board.not_updated:
        headings.append(board.heading_of(failure.service))
    return "Not updated: " + ", ".join(headings)


def _by_service(merge_requests: list[MergeRequest], board: Board, faded: bool) -> list[ServiceView]:
    views: dict[str, list[MergeRequestView]] = {}
    for merge_request in merge_requests:
        views.setdefault(merge_request.service, []).append(_view(merge_request, board, faded))
    services = []
    for service, found in views.items():
        services.append(ServiceView(board.heading_of(service), found))
    return services


def _view(merge_request: MergeRequest, board: Board, faded: bool) -> MergeRequestView:
    details = [merge_request.project, merge_request.role.word, word_of(merge_request), *merge_request.address.notes()]
    return MergeRequestView(
        key=f"{merge_request.service} {merge_request.address.forge_host} {merge_request.project} {merge_request.reference}",
        summary=f"{merge_request.reference} · {merge_request.author}",
        title=merge_request.title,
        details=" · ".join(details),
        address=merge_request.address,
        service=board.heading_of(merge_request.service),
        look=look_of(merge_request, faded),
    )
