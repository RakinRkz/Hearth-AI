# Offline-AI 🧠🔌

A **private, offline AI assistant** — chat with local LLMs, ask questions over your own documents (RAG),
and search the web with AI-summarized results. No cloud, no API keys, your data stays on your machine.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

<!-- 👇 Add a screenshot or short GIF of a chat + a document Q&A. This matters most. -->
![demo](docs/demo.gif)

## Why
I wanted a fully local LLM assistant — useful without internet, private by default, and able to reason
over my own files. Built it end-to-end in Python on top of `llama.cpp`.

### For non-technical users / Install and use experience
There are many AI tools on the internet that are arguably better and feature rich. But all of them require 
significant setup, knowledge and trial and error - hassle / impossible for a regular user.
The aim of this app: just install it like any other regular software and start using.

## Features
- 💬 **Local LLM chat** — runs GGUF models fully offline via `llama-cpp-python`
- 📄 **Document RAG** — ask questions across your PDF / DOCX / TXT / MD files
- 🌐 **AI web search** — DuckDuckGo results, summarized by the local model (optional, when online)
- ⚡ **GPU acceleration** — CUDA (NVIDIA) and Metal (Apple) offload
- 🧩 **Guided setup** — a wizard downloads a starter model so you're chatting in minutes
- 🖥️ **Cross-platform** — Windows, Linux, macOS

## Tech
`Python` · `llama-cpp-python` (llama.cpp) · GGUF models · RAG (embeddings + retrieval) ·
document parsing (PDF/DOCX/TXT/MD) · DuckDuckGo search

## Quickstart
```bash
git clone https://github.com/RakinRkz/Offline-AI
cd Offline-AI
pip install -r requirements.txt
python setup.py        # guided model download (adjust to your actual entry point)
python app.py          # launch the assistant
