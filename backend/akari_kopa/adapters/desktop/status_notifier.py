import os

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib

from akari_kopa.adapters.desktop.markup import tool_tip
from akari_kopa.adapters.desktop.status_notifier_interfaces import INTERFACES
from akari_kopa.use_cases.desktop.ports import IconContent, MenuEntry

ITEM_PATH = "/StatusNotifierItem"
MENU_PATH = "/MenuBar"
WATCHER = "org.kde.StatusNotifierWatcher"
ITEM_INTERFACE = "org.kde.StatusNotifierItem"
MENU_INTERFACE = "com.canonical.dbusmenu"
CHANGED_SIGNALS = ("NewTitle", "NewIcon", "NewToolTip")
OWN_NAME_REPLACING_NONE = 4
ROOT = 0


def _appearance(content: IconContent) -> tuple:
    entries = []
    for entry in content.menu:
        entries.append((entry.label, entry.action is not None))
    return content.title, content.description, content.pixmaps, entries


def _nothing_to_update(arguments) -> GLib.Variant:
    return GLib.Variant("(b)", (False,))


def _no_group_to_update(arguments) -> GLib.Variant:
    return GLib.Variant("(aiai)", ([], []))


def _pixmaps(content: IconContent) -> list[tuple[int, int, bytes]]:
    return [(pixmap.width, pixmap.height, pixmap.argb) for pixmap in content.pixmaps]


class TrayIcon:
    _count = 0

    def __init__(self, item_id: str, content: IconContent):
        TrayIcon._count += 1
        self.item_id = item_id
        self.content = content
        self.revision = 1
        self.name = f"org.kde.StatusNotifierItem-{os.getpid()}-{TrayIcon._count}"
        self.menu_methods = {
            "GetLayout": self._get_layout,
            "GetGroupProperties": self._get_group_properties,
            "GetProperty": self._get_property,
            "Event": self._on_event,
            "EventGroup": self._on_event_group,
            "AboutToShow": _nothing_to_update,
            "AboutToShowGroup": _no_group_to_update,
        }
        self.connection = self._own_connection()
        self.registrations = self._serve_item_and_menu()
        self._take_name()
        self.register()

    def register(self) -> None:
        self.connection.call(
            WATCHER, "/StatusNotifierWatcher", WATCHER, "RegisterStatusNotifierItem",
            GLib.Variant("(s)", (self.name,)), None, Gio.DBusCallFlags.NONE, -1, None, None, None,
        )

    def update(self, content: IconContent) -> None:
        changed = _appearance(content) != _appearance(self.content)
        self.content = content
        if changed:
            self._announce_change()

    def close(self) -> None:
        for registration in self.registrations:
            self.connection.unregister_object(registration)
        self.connection.close_sync(None)

    def _own_connection(self) -> Gio.DBusConnection:
        address = Gio.dbus_address_get_for_bus_sync(Gio.BusType.SESSION, None)
        flags = Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION
        return Gio.DBusConnection.new_for_address_sync(address, flags, None, None)

    def _serve_item_and_menu(self) -> list[int]:
        return [
            self.connection.register_object(ITEM_PATH, INTERFACES.interfaces[0], self._item_call, self._item_property, None),
            self.connection.register_object(MENU_PATH, INTERFACES.interfaces[1], self._menu_call, self._menu_property, None),
        ]

    def _take_name(self) -> None:
        self.connection.call_sync(
            "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "RequestName",
            GLib.Variant("(su)", (self.name, OWN_NAME_REPLACING_NONE)), GLib.VariantType("(u)"), Gio.DBusCallFlags.NONE, -1, None,
        )

    def _announce_change(self) -> None:
        self.revision += 1
        for signal in CHANGED_SIGNALS:
            self.connection.emit_signal(None, ITEM_PATH, ITEM_INTERFACE, signal, None)
        self.connection.emit_signal(None, MENU_PATH, MENU_INTERFACE, "LayoutUpdated", GLib.Variant("(ui)", (self.revision, ROOT)))

    def _item_property(self, connection, sender, path, interface, name):
        content = self.content
        return {
            "Category": GLib.Variant("s", "ApplicationStatus"),
            "Id": GLib.Variant("s", self.item_id),
            "Title": GLib.Variant("s", content.title),
            "Status": GLib.Variant("s", "Active"),
            "WindowId": GLib.Variant("i", 0),
            "IconName": GLib.Variant("s", ""),
            "IconPixmap": GLib.Variant("a(iiay)", _pixmaps(content)),
            "OverlayIconName": GLib.Variant("s", ""),
            "AttentionIconName": GLib.Variant("s", ""),
            "IconThemePath": GLib.Variant("s", ""),
            "ToolTip": GLib.Variant("(sa(iiay)ss)", tool_tip(content)),
            "ItemIsMenu": GLib.Variant("b", True),
            "Menu": GLib.Variant("o", MENU_PATH),
        }.get(name)

    def _item_call(self, connection, sender, path, interface, method, parameters, invocation):
        if method == "Activate" and self.content.on_activate:
            self.content.on_activate()
        invocation.return_value(None)

    def _menu_property(self, connection, sender, path, interface, name):
        return {
            "Version": GLib.Variant("u", 3),
            "TextDirection": GLib.Variant("s", "ltr"),
            "Status": GLib.Variant("s", "normal"),
            "IconThemePath": GLib.Variant("as", []),
        }.get(name)

    def _menu_call(self, connection, sender, path, interface, method, parameters, invocation):
        answer = self.menu_methods.get(method)
        if answer is None:
            invocation.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", method)
            return
        invocation.return_value(answer(parameters.unpack()))

    def _get_layout(self, arguments):
        children = [GLib.Variant("(ia{sv}av)", (number, self._entry_properties(number), [])) for number in self._entry_ids()]
        return GLib.Variant("(u(ia{sv}av))", (self.revision, (ROOT, self._entry_properties(ROOT), children)))

    def _get_group_properties(self, arguments):
        found = []
        for entry_id in self._asked_ids(arguments[0]):
            if self._known(entry_id):
                found.append((entry_id, self._entry_properties(entry_id)))
        return GLib.Variant("(a(ia{sv}))", (found,))

    def _asked_ids(self, ids: list[int]):
        if ids:
            return ids
        return range(ROOT, len(self.content.menu) + 1)

    def _get_property(self, arguments):
        entry_id, name = arguments
        return GLib.Variant("(v)", (self._property_or_empty(entry_id, name),))

    def _property_or_empty(self, entry_id: int, name: str) -> GLib.Variant:
        if not self._known(entry_id):
            return GLib.Variant("s", "")
        value = self._entry_properties(entry_id).get(name)
        if value is None:
            return GLib.Variant("s", "")
        return value

    def _on_event(self, arguments):
        self._clicked(arguments[0], arguments[1])
        return None

    def _on_event_group(self, arguments):
        for entry_id, event, _data, _time in arguments[0]:
            self._clicked(entry_id, event)
        return GLib.Variant("(ai)", ([],))

    def _entry_ids(self) -> range:
        return range(1, len(self.content.menu) + 1)

    def _known(self, entry_id: int) -> bool:
        return ROOT <= entry_id <= len(self.content.menu)

    def _entry(self, entry_id: int) -> MenuEntry:
        return self.content.menu[entry_id - 1]

    def _entry_properties(self, entry_id: int) -> dict:
        if entry_id == ROOT:
            return {"children-display": GLib.Variant("s", "submenu")}
        entry = self._entry(entry_id)
        if entry.label is None:
            return {"type": GLib.Variant("s", "separator")}
        return {"label": GLib.Variant("s", entry.label.replace("_", "__")), "enabled": GLib.Variant("b", entry.action is not None)}

    def _clicked(self, entry_id: int, event: str) -> None:
        action = self._action_of(entry_id)
        if event == "clicked" and action:
            action()

    def _action_of(self, entry_id: int):
        if entry_id not in self._entry_ids():
            return None
        return self._entry(entry_id).action
