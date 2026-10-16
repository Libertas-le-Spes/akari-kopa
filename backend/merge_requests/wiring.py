from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from merge_requests.adapters.keyring.secret_tool import SecretTool
from merge_requests.adapters.services.azure_devops.azure_devops import AzureDevOps
from merge_requests.adapters.services.bitbucket.bitbucket import Bitbucket
from merge_requests.adapters.services.gitea.gitea import Gitea
from merge_requests.adapters.services.gitea.tea import Tea
from merge_requests.adapters.services.github.github import GitHub
from merge_requests.adapters.services.gitlab.gitlab import GitLab
from merge_requests.adapters.storage import locations
from merge_requests.adapters.storage.answer_folder import AnswerFolder
from merge_requests.adapters.transport.command_line import CommandLine
from merge_requests.adapters.transport.graphql_cli import GraphQlCli
from merge_requests.adapters.transport.https import Https
from merge_requests.use_cases.desktop.ports import Desktop
from merge_requests.use_cases.listing.listing import Listing
from merge_requests.use_cases.listing.ports import Clock, Service


@dataclass(frozen=True)
class App:
    listing: Listing


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def services(command_line: CommandLine, clock: Clock) -> list[Service]:
    return [
        GitLab(GraphQlCli(command_line, "glab")),
        GitHub(GraphQlCli(command_line, "gh")),
        Gitea(Tea(command_line)),
        Bitbucket(SecretTool(command_line), Https, clock),
        AzureDevOps(SecretTool(command_line), Https),
    ]


def open_app(answers: Path | None = None, clock: Clock = utc_now, command_line: CommandLine | None = None) -> App:
    command_line = command_line or CommandLine()
    return App(Listing(services(command_line, clock), AnswerFolder(answers or locations.answer_folder()), clock))


def desktop() -> Desktop:
    from merge_requests.adapters.desktop.linux_desktop import LinuxDesktop
    return LinuxDesktop()
