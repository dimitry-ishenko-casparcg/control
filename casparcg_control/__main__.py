import dbus, dbus.service, os
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from .tray import Tray

def show_logs(): print("show logs")

def main():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    loop = GLib.MainLoop()

    name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
    bus_name = dbus.service.BusName(name, bus)

    def start_server():
        print("start server")
        tray.set_running(True)

    def stop_server():
        print("stop server")
        tray.set_running(False)

    tray = Tray(bus, "/StatusNotifierItem", start_server=start_server, stop_server=stop_server,
        show_logs=show_logs, quit=loop.quit
    )

    watcher = bus.get_object("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher")
    watcher.RegisterStatusNotifierItem(name, dbus_interface="org.kde.StatusNotifierWatcher")

    loop.run()

if __name__ == "__main__": main()
