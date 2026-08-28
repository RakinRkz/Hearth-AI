#!/usr/bin/env python3
"""
Hearth AI - Local AI Chat Application

A cross-platform web-based chat application with:
- Local LLM inference via llama.cpp
- RAG (Retrieval-Augmented Generation) for document Q&A
- Web search integration via DuckDuckGo

Usage:
    python main.py [--host HOST] [--port PORT] [--reload]
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Hearth AI")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Path to GGUF model file"
    )
    return parser.parse_args()


def _force_utf8_output():
    """Make stdout/stderr UTF-8 safe.

    The status lines below use glyphs (checkmarks, a rocket) that do not exist
    in the legacy Windows code pages. When output is redirected - piped to a
    file, captured by a launcher, or run under the packaged build - Python
    falls back to the locale encoding (cp1252 on most Windows installs) and
    printing them raises UnicodeEncodeError, killing the app during startup.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def bootstrap(model_path=None):
    """Prepare directories, start services and mount static files.

    Shared by the console entry point and the tray launcher so the two cannot
    drift apart. Returns the configured FastAPI app.
    """
    from api.main import app, mount_static_files
    from api.dependencies import initialize_services
    from utils import paths

    print("=" * 50)
    print("Hearth AI - Local AI Application")
    print("=" * 50)

    # Create the writable directories before any service touches them. An
    # installed build writes to %LOCALAPPDATA% / ~/.local/share rather than to
    # its own install directory, which may be read-only.
    paths.ensure_dirs()
    print(paths.describe())

    print("\nInitializing services...")
    status = initialize_services(model_path=model_path)

    if status["llm"]:
        print("✓ LLM service ready")
    else:
        print("✗ LLM service failed:", status["errors"])

    if status["embedding"]:
        print("✓ Embedding service ready")

    if status["rag"]:
        print("✓ RAG service ready")

    if status["search"]:
        print("✓ Search service ready")

    mount_static_files(app)
    return app


def main():
    """Main entry point."""
    _force_utf8_output()
    args = parse_args()

    # Import here to avoid slow startup for --help
    import uvicorn
    from api.dependencies import shutdown_services

    app = bootstrap(model_path=args.model)
    
    print(f"\n🚀 Starting server at http://{args.host}:{args.port}")
    print(f"   API docs: http://{args.host}:{args.port}/docs")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        uvicorn.run(
            "api.main:app" if args.reload else app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info",
        )
    finally:
        print("\nShutting down services...")
        shutdown_services()
        print("Goodbye!")


if __name__ == "__main__":
    main()
