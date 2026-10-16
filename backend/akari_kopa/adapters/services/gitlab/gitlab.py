from dataclasses import replace
from datetime import timedelta

from akari_kopa.adapters.services.gitlab import query
from akari_kopa.adapters.services.gitlab.reading import ConversationReading, merge_request, repository_of
from akari_kopa.adapters.transport.graphql_cli import GraphQlCli
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import MINE, REVIEWING


class GitLab:
    name = "gitlab"
    asked_every = timedelta(0)

    def __init__(self, cli: GraphQlCli):
        self.cli = cli

    def is_set_up(self) -> bool:
        return self.cli.installed()

    def merge_requests(self) -> list[MergeRequest]:
        return [found for host in self.cli.hosts() for found in self._on(host)]

    def _on(self, host: str) -> list[MergeRequest]:
        me = self.cli.ask(host, query.BOARD)["data"]["currentUser"]
        reading = ConversationReading(me["username"])
        mine = [self._mine(host, node, reading) for node in me["authoredMergeRequests"]["nodes"]]
        reviewing = [merge_request(node, REVIEWING) for node in me["reviewRequestedMergeRequests"]["nodes"]]
        return mine + reviewing

    def _mine(self, host: str, node: dict, reading: ConversationReading) -> MergeRequest:
        discussions = self._all_discussions(host, node)
        return replace(merge_request(node, MINE), conversation=reading.conversation(discussions), repository=repository_of(node))

    def _all_discussions(self, host: str, node: dict) -> list[dict]:
        page = node["discussions"]
        discussions = list(page["nodes"])
        while page["pageInfo"]["hasNextPage"]:
            after = page["pageInfo"]["endCursor"]
            more = self.cli.ask(host, query.MORE_DISCUSSIONS, project=node["project"]["fullPath"], iid=node["iid"], after=after)
            page = more["data"]["project"]["mergeRequest"]["discussions"]
            discussions += page["nodes"]
        return discussions
