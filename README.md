# AI Chat App

A local, cross-platform AI chat application with RAG and web search capabilities. Now featuring a modern React web interface!

## Features

- 💬 **Chat** - Converse with local LLMs (no internet required)
- 📄 **RAG** - Upload documents (PDF, TXT, MD, DOCX) and ask questions
- 🌐 **Web Search** - Search the web via DuckDuckGo and get AI-summarized results
- 🖥️ **Cross-platform** - Works on Windows, Linux, and macOS
- 🌙 **Dark Mode** - Beautiful dark theme by default
- 🚀 **Web-based** - Access via browser at `http://127.0.0.1:8080`

## Requirements

- Python 3.11 or 3.10
- Node.js 18+ (for frontend development)
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

### 3. Build Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Run the App

```bash
python src/main.py
```

Then open **http://127.0.0.1:8080** in your browser.

### Development Mode

For frontend development with hot reload:

```bash
# Terminal 1: Start backend
python src/main.py --port 8080

# Terminal 2: Start frontend dev server
cd frontend
npm run dev
```

Then open **http://localhost:5173** (Vite proxies API requests to backend).

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
│   ├── main.py              # Entry point (uvicorn)
│   ├── api/                 # FastAPI routes & schemas
│   ├── services/            # Business logic (LLM, RAG, Search)
│   ├── models/              # Data models
│   └── utils/               # Utilities
├── frontend/
│   ├── src/                 # React + TypeScript source
│   ├── dist/                # Production build
│   └── package.json
├── models/                  # GGUF model files
├── data/
│   ├── conversations/       # Saved chats
│   └── vectorstore/         # Document embeddings
├── documents/               # Uploaded documents
└── requirements.txt
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ / FastAPI |
| Frontend | Vite + React 19 + TypeScript |
| Styling | Tailwind CSS v4 |
| LLM | llama-cpp-python |
| Vector Store | ChromaDB |
| Embeddings | fastembed (ONNX) |
| Web Search | DuckDuckGo (ddgs) |

## License

MIT
