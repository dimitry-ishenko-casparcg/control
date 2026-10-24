import dbus.service, os

####################
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ICON = os.path.join(_HERE, "default.png")
RUNNING_ICON = os.path.join(_HERE, "running.png")
STOPPED_ICON = os.path.join(_HERE, "stopped.png")

class Tray(dbus.service.Object):
    def __init__(self, conn, object_path):
        super().__init__(conn, object_path)

        self.props = {
            "Category": "ApplicationStatus",
            "Id": "casparcg-control",
            "Title": "CasparCG Control",
            "Status": "Active",
            "IconName": DEFAULT_ICON,
        }

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface): return self.props

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="ss", out_signature="v")
    def Get(self, interface, name): return self.props[name]

    @dbus.service.signal("org.kde.StatusNotifierItem", signature="")
    def NewIcon(self): pass
