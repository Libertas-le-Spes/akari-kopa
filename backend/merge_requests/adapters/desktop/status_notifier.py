import os

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib

from merge_requests.use_cases.desktop.ports import IconContent, MenuEntry

ITEM_PATH = "/StatusNotifierItem"
MENU_PATH = "/MenuBar"
WATCHER = "org.kde.StatusNotifierWatcher"
ITEM_INTERFACE = "org.kde.StatusNotifierItem"
MENU_INTERFACE = "com.canonical.dbusmenu"
CHANGED_SIGNALS = ("NewTitle", "NewIcon", "NewToolTip")
OWN_NAME_REPLACING_NONE = 4
ROOT = 0

INTERFACES = Gio.DBusNodeInfo.new_for_xml("""
<node>
  <interface name="org.kde.StatusNotifierItem">
    <property name="Category" type="s" access="read"/>
    <property name="Id" type="s" access="read"/>
    <property name="Title" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="WindowId" type="i" access="read"/>
    <property name="IconName" type="s" access="read"/>
    <property name="IconPixmap" type="a(iiay)" access="read"/>
    <property name="OverlayIconName" type="s" access="read"/>
    <property name="AttentionIconName" type="s" access="read"/>
    <property name="IconThemePath" type="s" access="read"/>
    <property name="ToolTip" type="(sa(iiay)ss)" access="read"/>
    <property name="ItemIsMenu" type="b" access="read"/>
    <property name="Menu" type="o" access="read"/>
    <method name="ContextMenu"><arg name="x" type="i" direction="in"/><arg name="y" type="i" direction="in"/></method>
    <method name="Activate"><arg name="x" type="i" direction="in"/><arg name="y" type="i" direction="in"/></method>
    <method name="SecondaryActivate"><arg name="x" type="i" direction="in"/><arg name="y" type="i" direction="in"/></method>
    <method name="Scroll"><arg name="delta" type="i" direction="in"/><arg name="orientation" type="s" direction="in"/></method>
    <signal name="NewTitle"/>
    <signal name="NewIcon"/>
    <signal name="NewToolTip"/>
    <signal name="NewStatus"><arg name="status" type="s"/></signal>
  </interface>
  <interface name="com.canonical.dbusmenu">
    <property name="Version" type="u" access="read"/>
    <property name="TextDirection" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="IconThemePath" type="as" access="read"/>
    <method name="GetLayout">
      <arg name="parentId" type="i" direction="in"/>
      <arg name="recursionDepth" type="i" direction="in"/>
      <arg name="propertyNames" type="as" direction="in"/>
      <arg name="revision" type="u" direction="out"/>
      <arg name="layout" type="(ia{sv}av)" direction="out"/>
    </method>
    <method name="GetGroupProperties">
      <arg name="ids" type="ai" direction="in"/>
      <arg name="propertyNames" type="as" direction="in"/>
      <arg name="properties" type="a(ia{sv})" direction="out"/>
    </method>
    <method name="GetProperty">
      <arg name="id" type="i" direction="in"/>
      <arg name="name" type="s" direction="in"/>
      <arg name="value" type="v" direction="out"/>
    </method>
    <method name="Event">
      <arg name="id" type="i" direction="in"/>
      <arg name="eventId" type="s" direction="in"/>
      <arg name="data" type="v" direction="in"/>
      <arg name="timestamp" type="u" direction="in"/>
    </method>
    <method name="EventGroup">
      <arg name="events" type="a(isvu)" direction="in"/>
      <arg name="idErrors" type="ai" direction="out"/>
    </method>
    <method name="AboutToShow">
      <arg name="id" type="i" direction="in"/>
      <arg name="needUpdate" type="b" direction="out"/>
    </method>
    <method name="AboutToShowGroup">
      <arg name="ids" type="ai" direction="in"/>
      <arg name="updatesNeeded" type="ai" direction="out"/>
      <arg name="idErrors" type="ai" direction="out"/>
    </method>
    <signal name="ItemsPropertiesUpdated">
      <arg name="updatedProps" type="a(ia{sv})"/>
      <arg name="removedProps" type="a(ias)"/>
    </signal>
    <signal name="LayoutUpdated">
      <arg name="revision" type="u"/>
      <arg name="parent" type="i"/>
    </signal>
  </interface>
</node>
""")


def _appearance(content: IconContent) -> tuple:
    return content.title, content.description, content.pixmaps, [(entry.label, entry.action is not None) for entry in content.menu]


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
            "AboutToShow": lambda arguments: GLib.Variant("(b)", (False,)),
            "AboutToShowGroup": lambda arguments: GLib.Variant("(aiai)", ([], [])),
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
            "ToolTip": GLib.Variant("(sa(iiay)ss)", ("", [], content.title, content.description)),
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
        ids = arguments[0] or range(ROOT, len(self.content.menu) + 1)
        return GLib.Variant("(a(ia{sv}))", ([(entry_id, self._entry_properties(entry_id)) for entry_id in ids if self._known(entry_id)],))

    def _get_property(self, arguments):
        entry_id, name = arguments
        value = self._entry_properties(entry_id).get(name) if self._known(entry_id) else None
        return GLib.Variant("(v)", (value or GLib.Variant("s", ""),))

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
        return self._entry(entry_id).action if entry_id in self._entry_ids() else None
