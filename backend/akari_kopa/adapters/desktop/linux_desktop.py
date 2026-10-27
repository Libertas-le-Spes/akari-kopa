import hashlib
import signal
import sys
import threading
from typing import Callable

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib

from akari_kopa.adapters.desktop.markup import notice
from akari_kopa.adapters.desktop.status_notifier import WATCHER, TrayIcon
from akari_kopa.attention.merge_request.web_address import WebAddress
from akari_kopa.use_cases.desktop.ports import IconContent

def _on_signal(number: int, then: Callable[[], None]) -> None:
    try:
        gi.require_version("GLibUnix", "2.0")
        from gi.repository import GLibUnix
        GLibUnix.signal_add(GLib.PRIORITY_DEFAULT, number, then)
    except (ImportError, ValueError):
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, number, then)


class LinuxDesktop:
    def __init__(self):
        self.session = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.loop = GLib.MainLoop()

    def show_icon(self, key: str, content: IconContent) -> TrayIcon:
        return TrayIcon("merge-request-" + hashlib.sha1(key.encode()).hexdigest()[:12], content)

    def notify(self, summary: str, body: str) -> None:
        self.session.call(
            "org.freedesktop.Notifications", "/org/freedesktop/Notifications", "org.freedesktop.Notifications", "Notify",
            GLib.Variant("(susssasa{sv}i)", notice(summary, body)),
            None, Gio.DBusCallFlags.NONE, -1, None, None, None,
        )

    def open_in_browser(self, address: WebAddress) -> None:
        try:
            Gio.AppInfo.launch_default_for_uri(address.text, None)
        except GLib.Error as error:
            print(f"could not open {address.text}: {error.message}", file=sys.stderr)

    def when_tray_returns(self, then: Callable[[], None]) -> None:
        Gio.bus_watch_name_on_connection(self.session, WATCHER, Gio.BusNameWatcherFlags.NONE, _ignoring_details(then), None)

    def every(self, seconds: int, then: Callable[[], None]) -> None:
        GLib.timeout_add_seconds(seconds, _again_and_again, then)

    def in_background(self, work: Callable[[], object], then: Callable[[object], None]) -> None:
        threading.Thread(target=_work_then_hand_back, args=(work, then), daemon=True).start()

    def run_until_stopped(self) -> None:
        for number in (signal.SIGINT, signal.SIGTERM):
            _on_signal(number, self.loop.quit)
        self.loop.run()


def _once(then: Callable[[object], None], result: object) -> bool:
    then(result)
    return False


def _again_and_again(then: Callable[[], None]) -> bool:
    then()
    return True


def _work_then_hand_back(work: Callable[[], object], then: Callable[[object], None]) -> None:
    GLib.idle_add(_once, then, work())


def _ignoring_details(then: Callable[[], None]):
    def appeared(*details) -> None:
        then()
    return appeared
