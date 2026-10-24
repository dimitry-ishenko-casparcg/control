import dbus.service, os

_HERE = os.path.dirname(os.path.abspath(__file__))

####################
ITEMS = {
    1: { "label": "Start Server", "callback": "start_server" },
    2: { "label": "Stop Server",  "callback": "stop_server" },
    3: { "label": "Show logs",    "callback": "show_logs" },
    4: { "label": "Quit",         "callback": "quit" },
}
MENU_PATH = "/MenuBar"

class Menu(dbus.service.Object):
    def __init__(self, conn, object_path, callbacks):
        super().__init__(conn, object_path)
        self._callbacks = callbacks
        self._revision = 1

        self.props = {
            "Version": dbus.UInt32(3),
            "TextDirection": "ltr",
            "Status": "normal"
        }

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface): return self.props

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="ss", out_signature="v")
    def Get(self, interface, name): return self.props[name]

    @dbus.service.method("com.canonical.dbusmenu", in_signature="iias", out_signature="u(ia{sv}av)")
    def GetLayout(self, parent, depth, names):
        children = dbus.Array([
            dbus.Struct(
                (dbus.Int32(id), dbus.Dictionary(props, signature="sv"), dbus.Array([], signature="v")),
                signature="ia{sv}av",
                variant_level=1,
            )
            for id, props in ITEMS.items()
        ], signature="v")
        return self._revision, (0, { "children-display": "submenu" }, children)

    @dbus.service.method("com.canonical.dbusmenu", in_signature="aias", out_signature="a(ia{sv})")
    def GetGroupProperties(self, ids, names): return list(ITEMS.items())

    @dbus.service.method("com.canonical.dbusmenu", in_signature="i", out_signature="b")
    def AboutToShow(self, item_id): return False

    @dbus.service.method("com.canonical.dbusmenu", in_signature="isvu")
    def Event(self, item_id, event, data, timestamp):
        if event == "clicked":
            callback = self._callbacks.get(ITEMS[item_id]["callback"])
            if callback: callback()

    def set_enabled(self, callback_name, enabled):
        id = next(id for id, item in ITEMS.items() if item["callback"] == callback_name)
        ITEMS[id]["enabled"] = enabled

        self._revision += 1
        self.LayoutUpdated(self._revision, 0)

    @dbus.service.signal("com.canonical.dbusmenu", signature="ui")
    def LayoutUpdated(self, revision, parent): pass

####################
DEFAULT_ICON = os.path.join(_HERE, "default.png")
RUNNING_ICON = os.path.join(_HERE, "running.png")
STOPPED_ICON = os.path.join(_HERE, "stopped.png")

class Tray(dbus.service.Object):
    def __init__(self, conn, object_path, **callbacks):
        super().__init__(conn, object_path)
        self._menu = Menu(conn, MENU_PATH, callbacks)

        self.props = {
            "Category": "ApplicationStatus",
            "Id": "casparcg-control",
            "Title": "CasparCG Control",
            "Status": "Active",
            "IconName": DEFAULT_ICON,
            "Menu": dbus.ObjectPath(MENU_PATH),
        }

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface): return self.props

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="ss", out_signature="v")
    def Get(self, interface, name): return self.props[name]

    def set_running(self, running):
        self.props["IconName"] = RUNNING_ICON if running else STOPPED_ICON
        self.NewIcon()

        self._menu.set_enabled("start_server", not running)
        self._menu.set_enabled("stop_server", running)

    @dbus.service.signal("org.kde.StatusNotifierItem", signature="")
    def NewIcon(self): pass
