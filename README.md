# AI Chat App

A local, cross-platform AI chat application with RAG and web search capabilities.

## Features

- 💬 **Chat** - Converse with local LLMs (no internet required)
- 📄 **RAG** - Upload documents (PDF, TXT, MD, DOCX) and ask questions
- 🌐 **Web Search** - Search the web via DuckDuckGo and get AI-summarized results
- 🖥️ **Cross-platform** - Works on Windows, Linux, and macOS
- 🚀 **Easy Setup** - Built-in model downloader for beginners

## Requirements

- Python 3.11+
- 4GB+ RAM (8GB+ recommended for larger models)

## Quick Start

### 1. Create Virtual Environment

```bash
cd ai-app
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the App

```bash
python src/main.py
```

### 4. First Run Setup

On first launch, a **Setup Wizard** will guide you:

1. Click **"Download & Install"** to download the recommended model (~2.4GB)
2. Wait for the download to complete
3. Start chatting!

**Or skip the wizard** and manually load your own GGUF model from Settings.

## Available Models

The Setup Wizard offers these recommended models:

| Model | Size | Best For |
|-------|------|----------|
| **Phi-3.5 Mini** (default) | ~2.4GB | General chat, coding, reasoning |
| Llama 3.2 3B | ~2.0GB | Everyday tasks, fast responses |
| Qwen2.5 3B | ~2.0GB | Multilingual, coding |
| TinyLlama 1.1B | ~669MB | Low-end hardware, quick tests |

You can also download models from [HuggingFace](https://huggingface.co/models?search=gguf) and load them manually.

## GPU Acceleration

### NVIDIA (CUDA)

```bash
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### Apple Silicon (Metal)

```bash
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

## Usage

### Chat Mode
Simply type your message and press Enter or click Send.

### RAG Mode
1. Select "📄 RAG (Documents)" mode in the sidebar
2. Click "+ Upload" to add documents
3. Ask questions about your documents

### Web Search Mode
1. Select "🌐 Web Search" mode in the sidebar
2. Ask any question - the AI will search the web and summarize results

## Project Structure

```
ai-app/
├── src/
│   ├── main.py              # Entry point
│   ├── app.py               # Main application
│   ├── ui/                  # UI components
│   ├── services/            # Business logic
│   ├── models/              # Data models
│   └── utils/               # Utilities
├── models/                  # GGUF model files
├── data/
│   ├── conversations/       # Saved chats
│   └── vectorstore/         # Document embeddings
├── documents/               # Uploaded documents
└── requirements.txt
```

## License

MIT
