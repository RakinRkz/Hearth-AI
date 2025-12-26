#!/usr/bin/env python3
"""
AI Chat - Local AI Chat Application

A cross-platform desktop chat application with:
- Local LLM inference via llama.cpp
- RAG (Retrieval-Augmented Generation) for document Q&A
- Web search integration via DuckDuckGo

Usage:
    python main.py
"""

import sys
from pathlib import Path

# Add src to path for imports
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from ui import MainWindow


def main():
    """Main entry point."""
    window = MainWindow()
    window.mainloop()


if __name__ == "__main__":
    main()
