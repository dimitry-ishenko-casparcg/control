import dbus, dbus.service, os
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from .tray import Tray

def main():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    loop = GLib.MainLoop()

    name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
    bus_name = dbus.service.BusName(name, bus)

    Tray(bus, "/StatusNotifierItem")

    watcher = bus.get_object("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher")
    watcher.RegisterStatusNotifierItem(name, dbus_interface="org.kde.StatusNotifierWatcher")

    loop.run()

if __name__ == "__main__": main()
