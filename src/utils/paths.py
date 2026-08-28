"""Filesystem locations for bundled resources and writable user data.

Everything here exists because an installed application cannot write to its own
install directory. Two separate roots are needed:

* **Resources** - read-only files shipped with the app (the built frontend).
  When frozen these live inside the PyInstaller bundle, which is a temporary
  extraction directory, not a stable path on disk.
* **User data** - config, conversations, the vector store, downloaded models
  and uploaded documents. These must land somewhere the user can always write,
  per-platform convention:

      Windows   %LOCALAPPDATA%\\HearthAI
      macOS     ~/Library/Application Support/HearthAI
      Linux     $XDG_DATA_HOME/HearthAI  (or ~/.local/share/HearthAI)

Running from a source checkout keeps using the repo directories, so developing
against the repo behaves exactly as it always has - and, importantly, an
already-downloaded 2.4GB model does not become orphaned the first time someone
runs from source after this change.

Set HEARTH_DATA_DIR to override the user-data root anywhere (useful for tests,
and for a portable install that keeps its data beside the executable).
"""

import os
import sys
from pathlib import Path

APP_NAME = "HearthAI"


def is_frozen() -> bool:
    """True when running from a PyInstaller bundle rather than a checkout."""
    return getattr(sys, "frozen", False)


def resource_dir() -> Path:
    """Root for read-only files shipped with the app.

    Frozen builds unpack data into sys._MEIPASS; a source checkout serves them
    from the repository root.
    """
    if is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        # Fall back to the executable's own directory
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


def _platform_data_dir() -> Path:
    """Per-user writable directory following each platform's convention."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    # Linux and other POSIX
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return Path(base) / APP_NAME


def user_data_dir() -> Path:
    """Root for everything the user creates or downloads.

    An explicit HEARTH_DATA_DIR always wins. Otherwise frozen builds use the
    platform location and source checkouts stay in the repository.
    """
    override = os.environ.get("HEARTH_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if is_frozen():
        return _platform_data_dir()
    return Path(__file__).resolve().parent.parent.parent


def models_dir() -> Path:
    """Where .gguf model files live."""
    return user_data_dir() / "models"


def data_dir() -> Path:
    """Where conversations, the vector store and config.json live."""
    return user_data_dir() / "data"


def documents_dir() -> Path:
    """Where documents uploaded for RAG are stored."""
    return user_data_dir() / "documents"


def config_path() -> Path:
    """Full path to config.json."""
    return data_dir() / "config.json"


def frontend_dist_dir() -> Path:
    """The built React frontend served as static files."""
    return resource_dir() / "frontend" / "dist"


def ensure_dirs() -> None:
    """Create the writable directories the app expects to exist.

    Safe to call repeatedly. Called once during startup so that first run on a
    clean machine does not fail on a missing directory.
    """
    for path in (
        models_dir(),
        data_dir(),
        data_dir() / "conversations",
        data_dir() / "vectorstore",
        documents_dir(),
    ):
        path.mkdir(parents=True, exist_ok=True)


def describe() -> str:
    """One-line summary of resolved locations, for startup logging."""
    mode = "frozen" if is_frozen() else "source"
    return f"[paths] mode={mode} data={user_data_dir()} resources={resource_dir()}"
