from dataclasses import replace
from datetime import timedelta

from akari_kopa.adapters.services.github import query
from akari_kopa.adapters.services.github.reading import ConversationReading, merge_request, repository_of
from akari_kopa.adapters.transport.graphql_cli import GraphQlCli
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import MINE, REVIEWING


class GitHub:
    name = "github"
    heading = "GitHub"
    asked_every = timedelta(0)

    def __init__(self, cli: GraphQlCli):
        self.cli = cli

    def is_set_up(self) -> bool:
        return self.cli.installed()

    def merge_requests(self) -> list[MergeRequest]:
        return [found for host in self.cli.hosts() for found in self._on(host)]

    def _on(self, host: str) -> list[MergeRequest]:
        data = self.cli.ask(host, query.BOARD)["data"]
        reading = ConversationReading(data["viewer"]["login"])
        mine = [self._mine(host, node, reading) for node in data["viewer"]["pullRequests"]["nodes"]]
        reviewing = [merge_request(node, REVIEWING) for node in data["search"]["nodes"] if node]
        return mine + reviewing

    def _mine(self, host: str, node: dict, reading: ConversationReading) -> MergeRequest:
        details = {**node, **self.cli.ask(host, query.CONVERSATION, id=node["id"])["data"]["node"]}
        conversation = reading.conversation(details, self._all_threads(host, details))
        return replace(merge_request(node, MINE), conversation=conversation, repository=repository_of(details))

    def _all_threads(self, host: str, details: dict) -> list[dict]:
        page = details["reviewThreads"]
        threads = list(page["nodes"])
        while page["pageInfo"]["hasNextPage"]:
            page = self.cli.ask(host, query.MORE_THREADS, id=details["id"], after=page["pageInfo"]["endCursor"])["data"]["node"]["reviewThreads"]
            threads += page["nodes"]
        return threads
