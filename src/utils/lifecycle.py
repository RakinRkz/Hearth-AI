"""Application shutdown coordination.

The tray icon is the only way to stop Hearth AI, and Windows 11 files newly
registered tray icons behind the overflow chevron where most people will never
look. That leaves the app running invisibly with no obvious way to stop it, so
the web UI needs to be able to ask the process to exit.

The API layer cannot stop the tray directly - it has no reference to it - so
the launcher registers a hook here and the API asks for shutdown through it.
When nothing is registered (running from source under main.py) the request is
simply reported as unsupported rather than pretending to succeed.
"""

import threading
from typing import Callable, Optional

_hook: Optional[Callable[[], None]] = None
_lock = threading.Lock()


def set_shutdown_hook(hook: Optional[Callable[[], None]]) -> None:
    """Register the callable that actually stops the application."""
    global _hook
    with _lock:
        _hook = hook


def can_shutdown() -> bool:
    """True when something is able to act on a shutdown request."""
    with _lock:
        return _hook is not None


def request_shutdown(delay: float = 0.5) -> bool:
    """Ask the application to stop, shortly.

    Deliberately deferred: the caller is normally an HTTP handler, and the
    response has to reach the browser before the server stops serving,
    otherwise the UI sees a dropped connection instead of a clean goodbye.

    Returns False when no launcher registered a hook.
    """
    with _lock:
        hook = _hook
    if hook is None:
        return False

    threading.Timer(delay, hook).start()
    return True
