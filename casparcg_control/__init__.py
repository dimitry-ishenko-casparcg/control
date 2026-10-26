import dbus.service, os, subprocess
from gi.repository import GLib

__version__ = "0.3"

ICON_DIR = os.path.dirname(os.path.abspath(__file__))
ITEMS = {
    1: { "label": "Start Server", "icon-name": "start", "callback": "start_server" },
    2: { "label": "Stop Server",  "icon-name":  "stop", "callback": "stop_server" },
    3: { "label": "Show Logs",    "icon-name":  "logs", "callback": "show_logs" },
    4: { "label": "Quit",         "icon-name":  "quit", "callback": "quit" },
}
OBJECT_PATH = "/StatusNotifierItem"
MENU_PATH = "/MenuBar"

IFACE_DBUS_PROPERTIES = "org.freedesktop.DBus.Properties"
IFACE_DBUS_MENU = "com.canonical.dbusmenu"
IFACE_STATUS_NOTIFIER = "org.kde.StatusNotifierItem"

def launch(cmd): subprocess.Popen(cmd)

####################
class Menu(dbus.service.Object):
    def __init__(self, conn, object_path, callbacks):
        super().__init__(conn, object_path)
        self._callbacks = callbacks
        self._revision = 1

        self.props = {
            "Version": dbus.UInt32(2),
            "TextDirection": "ltr",
            "Status": "normal",
            "IconThemePath": dbus.Array([ICON_DIR], signature="s"),
        }

    @dbus.service.method(IFACE_DBUS_PROPERTIES, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface): return self.props

    @dbus.service.method(IFACE_DBUS_PROPERTIES, in_signature="ss", out_signature="v")
    def Get(self, interface, name): return self.props[name]

    @dbus.service.method(IFACE_DBUS_MENU, in_signature="iias", out_signature="u(ia{sv}av)")
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

    @dbus.service.method(IFACE_DBUS_MENU, in_signature="aias", out_signature="a(ia{sv})")
    def GetGroupProperties(self, ids, names): return list(ITEMS.items())

    @dbus.service.method(IFACE_DBUS_MENU, in_signature="i", out_signature="b")
    def AboutToShow(self, item_id): return False

    @dbus.service.method(IFACE_DBUS_MENU, in_signature="isvu")
    def Event(self, item_id, event, data, timestamp):
        if event == "clicked":
            callback = self._callbacks.get(ITEMS[item_id]["callback"])
            if callback: callback()

    def set_enabled(self, callback_name, enabled):
        id = next(id for id, item in ITEMS.items() if item["callback"] == callback_name)
        ITEMS[id]["enabled"] = enabled

        self._revision += 1
        self.LayoutUpdated(self._revision, 0)

    @dbus.service.signal(IFACE_DBUS_MENU, signature="ui")
    def LayoutUpdated(self, revision, parent): pass

####################
class Tray(dbus.service.Object):
    def __init__(self, conn, **callbacks):
        super().__init__(conn, OBJECT_PATH)

        self._menu = Menu(conn, MENU_PATH, callbacks)
        self.props = {
            "Category": "ApplicationStatus",
            "Id": "casparcg-control",
            "Title": "CasparCG Control",
            "Status": "Active",
            "IconThemePath": ICON_DIR,
            "IconName": "default",
            "Menu": dbus.ObjectPath(MENU_PATH),
        }

    @dbus.service.method(IFACE_DBUS_PROPERTIES, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface): return self.props

    @dbus.service.method(IFACE_DBUS_PROPERTIES, in_signature="ss", out_signature="v")
    def Get(self, interface, name): return self.props[name]

    def set_running(self, running):
        self.props["IconName"] = "running" if running else "stopped"
        self.NewIcon()

        self._menu.set_enabled("start_server", not running)
        self._menu.set_enabled("stop_server", running)

    @dbus.service.signal(IFACE_STATUS_NOTIFIER, signature="")
    def NewIcon(self): pass

####################
class Proc:
    def __init__(self, cmd, on_running=None):
        self.cmd = cmd
        self.on_running = on_running

        self._proc  = None
        self._state = None
        self._run   = False
        self._stop  = 0

        GLib.timeout_add(500, self._poll)

    def start(self): self._run = True
    def stop(self): self._run = False

    def running(self):
        return self._proc is not None and self._proc.poll() is None

    def _poll(self):
        running = self.running()
        if running != self._state:
            self._state = running
            if self.on_running: self.on_running(running)

        if self._run and not running:
            self._proc = subprocess.Popen(self.cmd)
        elif not self._run and running:
            self._stop += 1
            self._proc.kill() if self._stop > 5 else self._proc.terminate()
        else: self._stop = 0

        return True
