import os
from collections import namedtuple

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib

ITEM_PATH = "/StatusNotifierItem"
MENU_PATH = "/MenuBar"
WATCHER = "org.kde.StatusNotifierWatcher"

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

MenuEntry = namedtuple("MenuEntry", "label action")
Content = namedtuple("Content", "title description pixmaps menu on_activate")

SEPARATOR = MenuEntry(None, None)


def _appearance(content):
    return (
        content.title,
        content.description,
        content.pixmaps,
        [(entry.label, entry.action is not None) for entry in content.menu],
    )


class TrayIcon:
    _count = 0

    def __init__(self, item_id, content):
        TrayIcon._count += 1
        self.item_id = item_id
        self.content = content
        self.revision = 1
        self.name = "org.kde.StatusNotifierItem-%d-%d" % (os.getpid(), TrayIcon._count)
        address = Gio.dbus_address_get_for_bus_sync(Gio.BusType.SESSION, None)
        self.connection = Gio.DBusConnection.new_for_address_sync(
            address,
            Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,
            None,
            None,
        )
        self.registrations = [
            self.connection.register_object(
                ITEM_PATH, INTERFACES.interfaces[0], self._item_call, self._item_property, None
            ),
            self.connection.register_object(
                MENU_PATH, INTERFACES.interfaces[1], self._menu_call, self._menu_property, None
            ),
        ]
        self.connection.call_sync(
            "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "RequestName",
            GLib.Variant("(su)", (self.name, 4)), GLib.VariantType("(u)"),
            Gio.DBusCallFlags.NONE, -1, None,
        )
        self.register()

    def register(self):
        self.connection.call(
            WATCHER, "/StatusNotifierWatcher", WATCHER, "RegisterStatusNotifierItem",
            GLib.Variant("(s)", (self.name,)), None, Gio.DBusCallFlags.NONE, -1, None, None, None,
        )

    def update(self, content):
        changed = _appearance(content) != _appearance(self.content)
        self.content = content
        if not changed:
            return
        self.revision += 1
        for signal in ("NewTitle", "NewIcon", "NewToolTip"):
            self.connection.emit_signal(None, ITEM_PATH, "org.kde.StatusNotifierItem", signal, None)
        self.connection.emit_signal(
            None, MENU_PATH, "com.canonical.dbusmenu", "LayoutUpdated",
            GLib.Variant("(ui)", (self.revision, 0)),
        )

    def close(self):
        for registration in self.registrations:
            self.connection.unregister_object(registration)
        self.connection.close_sync(None)

    def _item_property(self, connection, sender, path, interface, name):
        content = self.content
        values = {
            "Category": GLib.Variant("s", "ApplicationStatus"),
            "Id": GLib.Variant("s", self.item_id),
            "Title": GLib.Variant("s", content.title),
            "Status": GLib.Variant("s", "Active"),
            "WindowId": GLib.Variant("i", 0),
            "IconName": GLib.Variant("s", ""),
            "IconPixmap": GLib.Variant("a(iiay)", content.pixmaps),
            "OverlayIconName": GLib.Variant("s", ""),
            "AttentionIconName": GLib.Variant("s", ""),
            "IconThemePath": GLib.Variant("s", ""),
            "ToolTip": GLib.Variant("(sa(iiay)ss)", ("", [], content.title, content.description)),
            "ItemIsMenu": GLib.Variant("b", True),
            "Menu": GLib.Variant("o", MENU_PATH),
        }
        return values.get(name)

    def _item_call(self, connection, sender, path, interface, method, parameters, invocation):
        if method == "Activate" and self.content.on_activate:
            self.content.on_activate()
        invocation.return_value(None)

    def _menu_property(self, connection, sender, path, interface, name):
        values = {
            "Version": GLib.Variant("u", 3),
            "TextDirection": GLib.Variant("s", "ltr"),
            "Status": GLib.Variant("s", "normal"),
            "IconThemePath": GLib.Variant("as", []),
        }
        return values.get(name)

    def _entry_properties(self, entry_id):
        if entry_id == 0:
            return {"children-display": GLib.Variant("s", "submenu")}
        entry = self.content.menu[entry_id - 1]
        if entry.label is None:
            return {"type": GLib.Variant("s", "separator")}
        return {
            "label": GLib.Variant("s", entry.label.replace("_", "__")),
            "enabled": GLib.Variant("b", entry.action is not None),
        }

    def _layout(self):
        children = [
            GLib.Variant("(ia{sv}av)", (number, self._entry_properties(number), []))
            for number in range(1, len(self.content.menu) + 1)
        ]
        return (0, self._entry_properties(0), children)

    def _known(self, entry_id):
        return 0 <= entry_id <= len(self.content.menu)

    def _menu_call(self, connection, sender, path, interface, method, parameters, invocation):
        arguments = parameters.unpack()
        if method == "GetLayout":
            invocation.return_value(GLib.Variant("(u(ia{sv}av))", (self.revision, self._layout())))
        elif method == "GetGroupProperties":
            ids = arguments[0] or range(0, len(self.content.menu) + 1)
            properties = [(entry_id, self._entry_properties(entry_id)) for entry_id in ids if self._known(entry_id)]
            invocation.return_value(GLib.Variant("(a(ia{sv}))", (properties,)))
        elif method == "GetProperty":
            entry_id, name = arguments
            value = self._entry_properties(entry_id).get(name) if self._known(entry_id) else None
            invocation.return_value(GLib.Variant("(v)", (value or GLib.Variant("s", ""),)))
        elif method == "Event":
            self._event(arguments[0], arguments[1])
            invocation.return_value(None)
        elif method == "EventGroup":
            for entry_id, event, _data, _time in arguments[0]:
                self._event(entry_id, event)
            invocation.return_value(GLib.Variant("(ai)", ([],)))
        elif method == "AboutToShow":
            invocation.return_value(GLib.Variant("(b)", (False,)))
        elif method == "AboutToShowGroup":
            invocation.return_value(GLib.Variant("(aiai)", ([], [])))
        else:
            invocation.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", method)

    def _event(self, entry_id, event):
        if event != "clicked" or not 1 <= entry_id <= len(self.content.menu):
            return
        action = self.content.menu[entry_id - 1].action
        if action:
            action()
