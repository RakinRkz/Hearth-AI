# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Hearth AI.

Build with the wrapper scripts, not directly -- they build the frontend
first, which this spec assumes already exists:

    ./build.sh      (Linux/macOS)
    build.bat       (Windows)

Note: llama-cpp-python, chromadb and fastembed all ship native libraries and
ONNX model metadata that PyInstaller cannot discover by static analysis, so
they are collected wholesale below.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

APP_NAME = "HearthAI"

block_cipher = None

datas = []
binaries = []
hiddenimports = []

# Native / data-heavy dependencies PyInstaller cannot trace on its own.
for pkg in ("llama_cpp", "chromadb", "fastembed", "onnxruntime", "tokenizers"):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception as exc:  # package genuinely absent from the venv
        print(f"[build.spec] warning: could not collect {pkg}: {exc}")

# uvicorn resolves its protocol/lifespan implementations by string name.
hiddenimports += collect_submodules("uvicorn")
hiddenimports += [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
]

# The built frontend. Served by mount_static_files() from _MEIPASS at runtime.
datas += [("frontend/dist", "frontend/dist")]


a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Desktop-era UI stack, no longer used by the web app.
    excludes=["tkinter", "customtkinter", "PIL", "matplotlib"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)
