from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from akari_kopa.adapters.dialogs.kdialog import Kdialog
from akari_kopa.adapters.dialogs.xdg_browser import XdgBrowser
from akari_kopa.adapters.dialogs.zenity import Zenity
from akari_kopa.adapters.keyring.secret_tool import SecretTool
from akari_kopa.adapters.services.azure_devops.azure_devops import AzureDevOps
from akari_kopa.adapters.services.bitbucket.bitbucket import Bitbucket
from akari_kopa.adapters.services.gitea.gitea import Gitea
from akari_kopa.adapters.services.gitea.tea import Tea
from akari_kopa.adapters.services.github.github import GitHub
from akari_kopa.adapters.services.gitlab.gitlab import GitLab
from akari_kopa.adapters.shortcuts.cinnamon import Cinnamon
from akari_kopa.adapters.shortcuts.environment import Environment, this_session
from akari_kopa.adapters.shortcuts.gnome import Gnome
from akari_kopa.adapters.shortcuts.gsettings import GSettings
from akari_kopa.adapters.shortcuts.hyprland import HyprlandConf, HyprlandLua, Omarchy
from akari_kopa.adapters.shortcuts.kde import Kde
from akari_kopa.adapters.shortcuts.mate import Mate
from akari_kopa.adapters.shortcuts.sway import Sway
from akari_kopa.adapters.shortcuts.xfce import Xfce
from akari_kopa.adapters.storage import locations
from akari_kopa.adapters.storage.answer_folder import AnswerFolder
from akari_kopa.adapters.transport.command_line import CommandLine
from akari_kopa.adapters.transport.graphql_cli import GraphQlCli
from akari_kopa.adapters.transport.https import Https
from akari_kopa.use_cases.choosing.ports import Browser, Chooser
from akari_kopa.use_cases.desktop.ports import Desktop
from akari_kopa.use_cases.listing.listing import Listing
from akari_kopa.use_cases.listing.ports import Clock, Service
from akari_kopa.use_cases.shortcut.shortcut_setup import ShortcutSetup

COMMAND = str(Path(__file__).resolve().parent.parent / "bin" / "akari-kopa")


@dataclass(frozen=True)
class App:
    listing: Listing
    chooser: Chooser | None
    browser: Browser
    shortcut: ShortcutSetup


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


def chooser(command_line: CommandLine) -> Chooser | None:
    return next((each for each in (Zenity(command_line), Kdialog(command_line)) if each.installed()), None)


def shortcut_homes(environment: Environment, command_line: CommandLine) -> list:
    choose = f"{COMMAND} choose"
    settings = GSettings(command_line)
    return [
        Omarchy(environment, command_line, choose),
        HyprlandLua(environment, command_line, choose),
        HyprlandConf(environment, command_line, choose),
        Sway(environment, command_line, choose),
        Kde(environment, command_line, choose),
        Gnome(environment, settings, choose),
        Cinnamon(environment, settings, choose),
        Mate(environment, settings, choose),
        Xfce(environment, command_line, choose),
    ]


def open_app(answers: Path | None = None, clock: Clock = utc_now, command_line: CommandLine | None = None,
             environment: Environment | None = None) -> App:
    command_line = command_line or CommandLine()
    listing = Listing(services(command_line, clock), AnswerFolder(answers or locations.answer_folder()), clock)
    homes = shortcut_homes(environment or this_session(), command_line)
    return App(listing, chooser(command_line), XdgBrowser(command_line), ShortcutSetup(homes))


def desktop() -> Desktop:
    from akari_kopa.adapters.desktop.linux_desktop import LinuxDesktop
    return LinuxDesktop()
