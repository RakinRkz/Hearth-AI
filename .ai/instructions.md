# Hearth AI - Development Instructions

## Project Overview
A local cross-platform desktop AI chat application with RAG and web search capabilities.

**Tech Stack:**
- Python 3.11+
- CustomTkinter (UI)
- llama-cpp-python (LLM inference)
- LangChain (orchestration)
- ChromaDB (vector store)
- sentence-transformers (embeddings)
- DuckDuckGo Search (web search)

## Project Structure

```
ai-app/
├── src/
│   ├── main.py                  # Entry point - runs the app
│   ├── app.py                   # App class that creates MainWindow
│   ├── ui/
│   │   ├── __init__.py          # Exports: MainWindow, ChatFrame, InputFrame, Sidebar, SettingsWindow, SetupWizard
│   │   ├── main_window.py       # Main window - wires all services and UI together
│   │   ├── chat_frame.py        # Scrollable chat with MessageBubble components
│   │   ├── input_frame.py       # Text input + send button, handles Enter key
│   │   ├── sidebar.py           # Mode selector, conversation list, document list
│   │   ├── settings_window.py   # Modal settings dialog with sliders
│   │   └── setup_wizard.py      # First-run setup wizard for model download
│   ├── services/
│   │   ├── __init__.py          # Exports all services
│   │   ├── llm_service.py       # LLMService - wraps llama-cpp-python
│   │   ├── embedding_service.py # EmbeddingService - wraps sentence-transformers
│   │   ├── rag_service.py       # RAGService - ChromaDB + document chunking
│   │   ├── search_service.py    # SearchService - DuckDuckGo integration
│   │   └── chat_service.py      # ChatService - orchestrates modes (Chat/RAG/Search)
│   ├── models/
│   │   ├── __init__.py          # Exports: Message, MessageRole, Conversation
│   │   ├── message.py           # Message dataclass with Source references
│   │   └── conversation.py      # Conversation with save/load/export
│   └── utils/
│       ├── __init__.py          # Exports config utilities
│       ├── config.py            # AppConfig dataclass + ConfigManager
│       ├── document_loader.py   # DocumentLoader for PDF, TXT, MD, DOCX
│       └── model_downloader.py  # ModelDownloader for auto-downloading models
├── models/                      # Store .gguf model files here
├── data/
│   ├── conversations/           # Saved conversation JSON files
│   ├── vectorstore/             # ChromaDB persistence
│   └── config.json              # User settings
├── documents/                   # User uploaded documents
├── requirements.txt             # Python dependencies
├── .ai/
│   ├── plan.md                  # Project plan
│   └── instructions.md          # This file
└── venv/                        # Virtual environment
```

## Architecture

```
┌─────────────────────────────────────────┐
│           CustomTkinter UI              │
│  MainWindow → ChatFrame, InputFrame,    │
│               Sidebar, SettingsWindow   │
├─────────────────────────────────────────┤
│           ChatService                   │
│  Orchestrates Chat/RAG/Search modes     │
├────────────┬────────────┬───────────────┤
│ RAGService │SearchService│  LLMService  │
│ (ChromaDB) │(DuckDuckGo) │(llama.cpp)   │
├────────────┴────────────┴───────────────┤
│         EmbeddingService                │
│      (sentence-transformers)            │
└─────────────────────────────────────────┘
```

## Key Services

### LLMService (`services/llm_service.py`)
- Wraps `llama-cpp-python` for local inference
- Methods: `load_model()`, `generate()`, `generate_stream()`, `generate_async()`
- Supports streaming with callbacks for UI updates
- Configure: `context_length`, `gpu_layers`, `temperature`, `top_p`

### EmbeddingService (`services/embedding_service.py`)
- Wraps `sentence-transformers` for text embeddings
- Default model: `all-MiniLM-L6-v2` (auto-downloads)
- Methods: `embed()`, `embed_batch()`

### RAGService (`services/rag_service.py`)
- Uses ChromaDB for vector storage (persisted locally)
- Methods: `add_document()`, `remove_document()`, `query()`, `get_context_for_query()`
- Uses DocumentLoader for PDF, TXT, MD, DOCX parsing
- Chunks documents with configurable size/overlap

### SearchService (`services/search_service.py`)
- Uses `duckduckgo-search` (no API key needed)
- Methods: `search()`, `get_context_for_query()`
- Returns: title, url, snippet for each result

### ChatService (`services/chat_service.py`)
- Orchestrates all other services
- Three modes: `ChatMode.CHAT`, `ChatMode.RAG`, `ChatMode.SEARCH`
- Manages conversations, auto-saves after each message
- Methods: `send_message()`, `send_message_stream()`, `send_message_async()`
- Injects context from RAG/Search into system prompt

## Data Models

### Message (`models/message.py`)
```python
@dataclass
class Message:
    role: MessageRole  # USER, ASSISTANT, SYSTEM
    content: str
    timestamp: datetime
    sources: List[Source]  # Citations for RAG/Search
    metadata: Dict[str, Any]
```

### Conversation (`models/conversation.py`)
```python
@dataclass
class Conversation:
    id: str  # UUID
    title: str  # Auto-generated from first message
    messages: List[Message]
    system_prompt: str
    # Methods: save(), load(), export_markdown()
```

## Configuration

### AppConfig (`utils/config.py`)
```python
@dataclass
class AppConfig:
    # Paths
    models_dir: str = "models"
    data_dir: str = "data"
    
    # LLM
    model_path: Optional[str] = None
    context_length: int = 4096
    max_tokens: int = 1024
    temperature: float = 0.7
    gpu_layers: int = 0  # 0=CPU, -1=all GPU
    
    # RAG
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 4
    
    # Search
    max_search_results: int = 5
    
    # UI
    theme: str = "dark"
```

Config is auto-saved to `data/config.json`.

## UI Components

### MainWindow (`ui/main_window.py`)
- Creates all services on init
- Wires callbacks between UI components and services
- Handles streaming: `_on_token_received()` updates chat in real-time
- Error handling with modal dialogs

### ChatFrame (`ui/chat_frame.py`)
- `MessageBubble` - individual message with optional sources
- `add_message()` - add complete message
- `start_streaming()` / `update_streaming()` / `finish_streaming()` - for streaming responses
- Auto-scrolls to bottom

### Sidebar (`ui/sidebar.py`)
- Mode radio buttons (Chat/RAG/Search)
- Conversation list with delete buttons
- Document list with upload button
- Model status indicator

## Running the App

```bash
# Activate virtual environment
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# For GPU support (optional):
# NVIDIA: CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python --force-reinstall
# macOS: CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall

# Run the app
python src/main.py
```

## Using the App

### First Run Setup
When you first launch the app, a **Setup Wizard** will guide you:

1. The wizard shows recommended models for download
2. Click "Download & Install" to download the default model (~2.4GB)
3. Wait for download to complete
4. The model loads automatically

**If you skip the wizard**, you can:
- Click Settings → "📥 Download Recommended Model" to open the wizard again
- Or manually browse for a .gguf model file

### Manual Model Setup

### Manual Model Setup
1. **Load a Model**: Settings → Browse for .gguf file → Load
2. **Chat**: Type message, press Enter or click Send
3. **RAG Mode**: 
   - Upload documents via sidebar
   - Select "RAG (Documents)" mode
   - Ask questions about your documents
4. **Search Mode**:
   - Select "Web Search" mode
   - Ask questions - app searches DuckDuckGo and summarizes

### Available Default Models

The Setup Wizard offers these recommended models:

| Model | Size | Description |
|-------|------|-------------|
| **Phi-3.5 Mini** (recommended) | ~2.4GB | Microsoft's excellent all-rounder for chat and coding |
| Llama 3.2 3B | ~2.0GB | Meta's efficient small model |
| Qwen2.5 3B | ~2.0GB | Strong multilingual capabilities |
| TinyLlama 1.1B | ~669MB | Ultra-lightweight for low-end hardware |

## Dependencies

```txt
# Core UI
customtkinter>=5.2.0
pillow>=10.0.0

# LLM
llama-cpp-python>=0.2.0

# LangChain & RAG
langchain>=0.3.0
langchain-community>=0.3.0
chromadb>=0.4.0
sentence-transformers>=2.2.0

# Document Loaders
pypdf>=3.0.0
python-docx>=1.0.0

# Web Search
duckduckgo-search>=6.0.0

# Config
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

## Model Recommendations

| Model | Size | RAM | Download |
|-------|------|-----|----------|
| Llama 3.2 3B Q4_K_M | ~2GB | 4GB | HuggingFace |
| Mistral 7B Q4_K_M | ~4GB | 8GB | HuggingFace |
| Phi-3 Mini Q4_K_M | ~2.4GB | 4GB | HuggingFace |

Download .gguf files from: https://huggingface.co/models?search=gguf

## Common Issues

### "No model loaded"
- Go to Settings, browse for a .gguf file, click Load

### Slow inference
- Use a smaller model or quantization (Q4_K_M)
- Enable GPU: set `gpu_layers=-1` in settings (requires CUDA/Metal build)

### Document not indexing
- Check file format is supported (PDF, TXT, MD, DOCX)
- Check console for errors

### Web search not working
- Requires internet connection
- DuckDuckGo may rate-limit; wait and retry

## Extending the App

### Add a new chat mode
1. Add mode to `ChatMode` enum in `chat_service.py`
2. Add handling in `ChatService._prepare_messages()`
3. Add radio button in `Sidebar`

### Add new document format
1. Add extension to `DocumentLoader.SUPPORTED_EXTENSIONS`
2. Add `_load_xxx()` method in `DocumentLoader`

### Change UI theme
- Modify colors in `ChatFrame`, `MessageBubble`, `Sidebar`
- CustomTkinter supports: "dark", "light", "system"

## File Locations

- **Conversations**: `data/conversations/{uuid}.json`
- **Vector DB**: `data/vectorstore/`
- **Config**: `data/config.json`
- **Models**: `models/*.gguf`
- **Uploaded docs**: tracked in vectorstore metadata

---

## Releasing / Packaging the App

### Overview
Use **PyInstaller** to create standalone executables. Users download and run - no Python needed.

### Build Files
- `build.spec` - PyInstaller configuration
- `build.sh` - Linux/macOS build script
- `build.bat` - Windows build script

### Build Commands

```bash
# Linux/macOS
chmod +x build.sh
./build.sh

# Windows
build.bat
```

### Output
```
dist/HearthAI/
├── HearthAI (or HearthAI.exe on Windows)
├── models/          # User puts .gguf files here
├── data/            # App data (created on first run)
├── documents/       # For uploaded docs
└── README.txt       # User instructions
```

### Distribution

**Linux:**
```bash
tar -czvf HearthAI-1.0.0-linux.tar.gz -C dist HearthAI
```

**Windows:**
```
Zip the dist/HearthAI folder → HearthAI-1.0.0-windows.zip
```

**macOS:**
```bash
# Creates .app bundle automatically
# Optionally create DMG with create-dmg tool
```

### Bundle Sizes (Approximate)
| Configuration | Size |
|---------------|------|
| CPU only | ~500 MB - 1 GB |
| With CUDA (GPU) | ~2-3 GB |
| + Model (7B Q4) | +4 GB |

### GPU Builds

For GPU acceleration, users need special builds:

**NVIDIA (CUDA):**
```bash
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python --force-reinstall
# Then build with PyInstaller
```

**macOS (Metal):**
```bash
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall
# Then build with PyInstaller
```

### Release Checklist
1. [ ] Test app runs correctly
2. [ ] Update version in `build.spec`
3. [ ] Run build script
4. [ ] Test the built executable
5. [ ] Create archives for each platform
6. [ ] Create GitHub release with:
   - CPU builds for Windows/Linux/macOS
   - (Optional) GPU builds
   - Release notes
   - Model download links

### Alternative: Nuitka (Smaller Builds)
```bash
pip install nuitka
nuitka --standalone --enable-plugin=tk-inter src/main.py
```
Produces smaller binaries but more complex setup.

