from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

from merge_requests.attention.merge_request.merge_request import MergeRequest
from merge_requests.use_cases.listing.board import Board, NotUpdated
from merge_requests.use_cases.listing.ports import Answers, Clock, Service, reason_for


@dataclass(frozen=True)
class Asked:
    merge_requests: list[MergeRequest]
    not_updated: NotUpdated | None = None


class Listing:
    def __init__(self, services: list[Service], answers: Answers, clock: Clock):
        self.services = services
        self.answers = answers
        self.clock = clock

    def board(self) -> Board:
        now = self.clock()
        set_up = [service for service in self.services if service.is_set_up()]
        with ThreadPoolExecutor(max_workers=max(1, len(set_up))) as pool:
            asked = list(pool.map(lambda service: self._ask(service, now), set_up))
        return Board(
            [merge_request for each in asked for merge_request in each.merge_requests if merge_request.on_the_bar(now)],
            [each.not_updated for each in asked if each.not_updated],
        )

    def _ask(self, service: Service, now: datetime) -> Asked:
        last = self.answers.last(service.name)
        if last and now - last.given < service.asked_every:
            return Asked(last.merge_requests)
        try:
            merge_requests = service.merge_requests()
        except Exception as error:
            return Asked(last.merge_requests if last else [], NotUpdated(service.name, reason_for(error)))
        self.answers.keep(service.name, merge_requests, now)
        return Asked(merge_requests)
