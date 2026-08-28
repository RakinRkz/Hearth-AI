"""System tray launcher for Hearth AI.

The console entry point (main.py) prints a URL and expects you to open it. That
is fine for development and wrong for someone who installed this like any other
application. This launcher is the installed-app front door: it starts the
server in the background, opens the browser once the server actually answers,
and leaves a tray icon as the visible sign that Hearth is running - and, just
as importantly, as the way to stop it.
"""

import os
import socket
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

HOST = "127.0.0.1"
DEFAULT_PORT = 8080
PORT_SCAN_LIMIT = 20


def port_is_free(port: int) -> bool:
    """True if we can bind the port right now.

    SO_REUSEADDR is deliberately not set: on Windows it permits binding a port
    that is already in use, which would defeat the check entirely.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((HOST, port))
            return True
        except OSError:
            return False


def find_free_port(preferred: int = DEFAULT_PORT) -> int:
    """First free port at or after `preferred`.

    A consumer app cannot assume 8080 is available - another Hearth window, or
    any other local server, may already hold it.
    """
    for candidate in range(preferred, preferred + PORT_SCAN_LIMIT):
        if port_is_free(candidate):
            return candidate
    raise RuntimeError(
        f"No free port between {preferred} and {preferred + PORT_SCAN_LIMIT - 1}"
    )


def wait_until_serving(port: int, timeout: float = 120.0) -> bool:
    """Block until the server accepts a connection, or give up.

    Model loading dominates startup and can take a while on a cold cache, so
    the browser must not open before there is something to show.
    """
    deadline = threading.Event()
    timer = threading.Timer(timeout, deadline.set)
    timer.start()
    try:
        while not deadline.is_set():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                if sock.connect_ex((HOST, port)) == 0:
                    return True
            deadline.wait(0.4)
        return False
    finally:
        timer.cancel()


class ServerThread(threading.Thread):
    """Runs uvicorn off the main thread.

    pystray needs the main thread for its message loop on Windows, so the
    server cannot have it. uvicorn.Server is used directly rather than
    uvicorn.run() because it exposes should_exit, which is the only clean way
    to stop it from another thread.
    """

    def __init__(self, app, port: int):
        super().__init__(name="hearth-server", daemon=True)
        import uvicorn

        self._server = uvicorn.Server(
            uvicorn.Config(app, host=HOST, port=port, log_level="warning")
        )

    def run(self) -> None:
        self._server.run()

    def stop(self, timeout: float = 10.0) -> None:
        self._server.should_exit = True
        self.join(timeout=timeout)


def load_icon_image():
    """The tray image, from the shipped asset with a drawn fallback."""
    from PIL import Image

    from utils import paths

    icon_file = paths.resource_dir() / "assets" / "hearth.png"
    if icon_file.exists():
        return Image.open(icon_file)

    # Missing asset should not stop the app launching
    sys.path.insert(0, str(paths.resource_dir() / "tools"))
    from make_icon import render

    return render(64)


def open_data_folder() -> None:
    """Reveal the writable data directory in the OS file browser."""
    from utils import paths

    target = str(paths.user_data_dir())
    if sys.platform == "win32":
        os.startfile(target)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target])
    else:
        subprocess.Popen(["xdg-open", target])


def main() -> int:
    from main import _force_utf8_output, bootstrap

    _force_utf8_output()

    import pystray

    port = find_free_port()
    url = f"http://{HOST}:{port}/"

    app = bootstrap()
    server = ServerThread(app, port)
    server.start()

    icon = pystray.Icon("hearth-ai", load_icon_image(), f"Hearth AI - {url}")

    def quit_app(_icon=None, _item=None):
        icon.visible = False
        icon.stop()

    icon.menu = pystray.Menu(
        pystray.MenuItem("Open Hearth AI", lambda: webbrowser.open(url), default=True),
        pystray.MenuItem("Open data folder", lambda: open_data_folder()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit Hearth AI", quit_app),
    )

    def on_ready(_icon):
        _icon.visible = True
        print("Tray icon ready")
        if wait_until_serving(port):
            print(f"Serving at {url} - opening browser")
            webbrowser.open(url)
        else:
            print("Server did not start in time; not opening a browser.")

    try:
        # Blocks on the main thread until quit_app stops it
        icon.run(setup=on_ready)
    finally:
        from api.dependencies import shutdown_services

        server.stop()
        shutdown_services()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
