from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from akari_kopa.adapters.dialogs.xdg_browser import XdgBrowser
from akari_kopa.adapters.dialogs.zenity import Zenity
from akari_kopa.adapters.services.azure_devops.az import Az
from akari_kopa.adapters.services.azure_devops.azure_devops import AzureDevOps
from akari_kopa.adapters.services.azure_devops.connection import azure_connection
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
from akari_kopa.adapters.shortcuts.text_files import TextFiles
from akari_kopa.adapters.shortcuts.xfce import Xfce
from akari_kopa.adapters.storage import locations
from akari_kopa.adapters.storage.answer_folder import AnswerFolder
from akari_kopa.adapters.storage.private_folder import PrivateFolder
from akari_kopa.adapters.transport.command_line import CommandLine
from akari_kopa.adapters.transport.graphql_cli import GraphQlCli
from akari_kopa.use_cases.choosing.ports import Browser, Chooser
from akari_kopa.use_cases.desktop.ports import Desktop
from akari_kopa.use_cases.listing.listing import Listing
from akari_kopa.use_cases.listing.ports import Service
from akari_kopa.use_cases.shortcut.shortcut_setup import ShortcutSetup

INSTALL_PATH = str(Path(__file__).resolve().parent.parent.parent)
COMMAND = f"{INSTALL_PATH}/backend/bin/akari-kopa"


@dataclass(frozen=True)
class App:
    listing: Listing
    chooser: Chooser | None
    browser: Browser
    shortcut: ShortcutSetup


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def services(command_line: CommandLine) -> list[Service]:
    return [
        GitLab(GraphQlCli(command_line, "glab", "../graphql")),
        GitHub(GraphQlCli(command_line, "gh", "graphql")),
        Gitea(Tea(command_line)),
        AzureDevOps(Az(command_line), azure_connection),
    ]


def chooser(command_line: CommandLine) -> Chooser | None:
    zenity = Zenity(command_line)
    if zenity.installed():
        return zenity
    return None


def shortcut_homes(environment: Environment, command_line: CommandLine) -> list:
    choose = f"{COMMAND} choose"
    settings = GSettings(command_line)
    files = TextFiles()
    return [
        Omarchy(environment, command_line, files, choose),
        HyprlandLua(environment, command_line, files, choose),
        HyprlandConf(environment, command_line, files, choose),
        Sway(environment, command_line, files, choose),
        Kde(environment, command_line, files, choose),
        Gnome(environment, settings, choose),
        Cinnamon(environment, settings, choose),
        Mate(environment, settings, choose),
        Xfce(environment, command_line, choose),
    ]


def open_app() -> App:
    command_line = CommandLine()
    listing = Listing(services(command_line), AnswerFolder(PrivateFolder(locations.answer_folder())), utc_now)
    homes = shortcut_homes(this_session(), command_line)
    return App(listing, chooser(command_line), XdgBrowser(command_line), ShortcutSetup(homes, INSTALL_PATH))


def desktop() -> Desktop:
    from akari_kopa.adapters.desktop.linux_desktop import LinuxDesktop
    return LinuxDesktop()
