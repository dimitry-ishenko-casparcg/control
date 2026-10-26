import os, signal
from gi.repository import GLib
from pathlib import Path
from . import launch, Notifier, Proc, Tray

def xdg(name, def_value): return Path(os.environ.get(name) or (Path.home() / def_value))
casparcg_log = xdg("XDG_STATE_HOME", ".local/state") / "casparcg-server/casparcg.log"

def show_logs():
    launch(["x-terminal-emulator", "-e", "tail", "-n", "+1", "-f", casparcg_log])

def main():
    ctx = GLib.MainContext.default()
    loop = GLib.MainLoop()

    notifier = Notifier()
    server = Proc(["casparcg-server"])

    tray = Tray(notifier.bus, start_server=server.start, stop_server=server.stop,
        show_logs=show_logs, quit=loop.quit)
    server.on_running = tray.set_running

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, loop.quit)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, loop.quit)

    loop.run()

    server.stop()
    while server.running(): ctx.iteration(True)

if __name__ == "__main__": main()
