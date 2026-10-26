import dbus, dbus.service, os, signal
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from pathlib import Path
from . import launch, Proc, Tray

def xdg(name, def_value): return Path(os.environ.get(name) or (Path.home() / def_value))
casparcg_log = xdg("XDG_STATE_HOME", ".local/state") / "casparcg-server/casparcg.log"

def show_logs():
    launch(["x-terminal-emulator", "-e", "tail", "-n", "+1", "-f", casparcg_log])

def main():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()

    ctx = GLib.MainContext.default()
    loop = GLib.MainLoop()

    name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
    bus_name = dbus.service.BusName(name, bus)

    server = Proc(["casparcg-server"])
    tray = Tray(bus, start_server=server.start, stop_server=server.stop,
        show_logs=show_logs, quit=loop.quit)
    server.on_running = tray.set_running

    watcher = bus.get_object("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher")
    watcher.RegisterStatusNotifierItem(name, dbus_interface="org.kde.StatusNotifierWatcher")

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, loop.quit)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, loop.quit)

    loop.run()

    server.stop()
    while server.running(): ctx.iteration(True)

if __name__ == "__main__": main()
