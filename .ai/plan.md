# Hearth AI - Project Plan

## Overview

A local **cross-platform** AI chat application with **RAG** and **web search** capabilities. Runs 100% locally using llama.cpp, accessed via browser at `127.0.0.1`.

**Supported Platforms:** Windows, Linux, macOS

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ / FastAPI |
| Frontend | Vite + React + TypeScript |
| Styling | Tailwind CSS + shadcn/ui |
| LLM | llama-cpp-python |
| Vector Store | ChromaDB |
| Embeddings | sentence-transformers |
| Web Search | DuckDuckGo (ddgs) |
| Documents | PDF, TXT, MD, DOCX |

## Features

- 💬 **Chat** - Direct conversation with local LLM, streaming responses
- 📄 **RAG** - Upload documents, ask questions with source citations
- 🌐 **Web Search** - Real-time search via DuckDuckGo, summarized by LLM
- 🌙 **Dark Mode** - Dark theme enabled by default

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 React Frontend (Vite)                       │
│        Tailwind CSS + shadcn/ui + React Context             │
├─────────────────────────────────────────────────────────────┤
│                    WebSocket + REST                         │
├─────────────────────────────────────────────────────────────┤
│                   FastAPI Backend                           │
│         /ws/chat (streaming) + /api/* (REST)                │
├──────────────┬──────────────────┬───────────────────────────┤
│  RAG Service │  Search Service  │   Chat Service            │
│  (Documents) │  (DuckDuckGo)    │   (Conversation)          │
├──────────────┴──────────────────┴───────────────────────────┤
│                      ChromaDB                               │
│              (Vector Store for Documents)                   │
├─────────────────────────────────────────────────────────────┤
│                   llama-cpp-python                          │
│            (LLM Inference + GPU Acceleration)               │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
Hearth-AI/
├── src/
│   ├── main.py                  # API entry point (uvicorn)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, CORS, static files
│   │   ├── dependencies.py      # Service singletons
│   │   ├── schemas.py           # Pydantic request/response models
│   │   └── routes/
│   │       ├── chat.py          # WebSocket /ws/chat
│   │       ├── conversations.py # REST /api/conversations
│   │       ├── documents.py     # REST /api/documents
│   │       └── settings.py      # REST /api/settings
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py       # LLM inference (existing)
│   │   ├── chat_service.py      # Chat orchestration (existing)
│   │   ├── rag_service.py       # RAG pipeline (existing)
│   │   ├── search_service.py    # Web search (existing)
│   │   └── embedding_service.py # Embeddings (existing)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── message.py           # Message data model (existing)
│   │   └── conversation.py      # Conversation model (existing)
│   └── utils/
│       ├── __init__.py
│       ├── config.py            # Configuration (existing)
│       └── document_loader.py   # Doc loaders (existing)
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # React entry point
│   │   ├── App.tsx              # Root component + providers
│   │   ├── contexts/
│   │   │   ├── ChatContext.tsx      # Messages, streaming state
│   │   │   ├── ConversationContext.tsx  # Conversation CRUD
│   │   │   └── SettingsContext.tsx  # Mode, theme, params
│   │   ├── hooks/
│   │   │   └── useChatSocket.ts # WebSocket connection
│   │   ├── components/
│   │   │   ├── ChatView.tsx     # Message list + scroll
│   │   │   ├── MessageBubble.tsx # User/assistant message
│   │   │   ├── MessageInput.tsx # Input + send button
│   │   │   ├── Sidebar.tsx      # Conversations + documents
│   │   │   └── SettingsDialog.tsx # Settings modal
│   │   └── lib/
│   │       └── api.ts           # REST API client
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── models/                       # GGUF models folder
├── data/
│   ├── conversations/
│   └── vectorstore/
├── documents/                    # User uploaded documents
└── requirements.txt
```

## Implementation Phases

### Phase 1: FastAPI Backend ✅
- [x] Create `src/api/main.py` with FastAPI app, CORS middleware
- [x] Create `src/api/dependencies.py` with service singletons
- [x] Create `src/api/schemas.py` with Pydantic models
- [x] Create WebSocket endpoint `/ws/chat` for streaming
- [x] Create REST routes for conversations, documents, settings
- [x] Create `src/main.py` entry point (uvicorn + static files)
- [x] Update `requirements.txt` (add fastapi, uvicorn, websockets)

### Phase 2: React Frontend Setup ✅
- [x] Scaffold Vite + React + TypeScript in `frontend/`
- [x] Add Tailwind CSS v4 with dark mode
- [x] Setup utility libraries (lucide-react, clsx, tailwind-merge)
- [x] Create base layout with sidebar + main area

### Phase 3: React Context & State ✅
- [x] Create `ChatContext` (messages, streaming, send/cancel)
- [x] Create `ConversationContext` (list, active, CRUD)
- [x] Create `SettingsContext` (mode, theme toggle, params)
- [x] Implement WebSocket connection in ChatContext

### Phase 4: UI Components ✅
- [x] Build `ChatView` with auto-scroll
- [x] Build `MessageBubble` (user/assistant variants)
- [x] Build `MessageInput` with send button + cancel
- [x] Build `Sidebar` with conversation list + mode selector
- [x] Build `SettingsDialog` with model/generation/about tabs

### Phase 5: Integration & Polish ✅
- [x] Connect frontend to backend API
- [x] Add source citations display for RAG
- [x] Add loading states and error handling
- [x] Test streaming + cancellation
- [ ] Implement document upload with drag-drop (optional)

### Phase 6: Cleanup & Distribution ✅
- [x] Remove `src/ui/` folder (CustomTkinter code)
- [x] Remove `src/app.py` (old CustomTkinter app)
- [x] Update README with new run instructions
- [x] Frontend builds to `frontend/dist/`

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ws/chat` | WebSocket | Streaming chat messages |
| `/api/conversations` | GET | List all conversations |
| `/api/conversations` | POST | Create new conversation |
| `/api/conversations/{id}` | GET | Load conversation |
| `/api/conversations/{id}` | DELETE | Delete conversation |
| `/api/documents` | GET | List uploaded documents |
| `/api/documents` | POST | Upload document |
| `/api/documents/{id}` | DELETE | Delete document |
| `/api/settings` | GET | Get current settings |
| `/api/settings` | PUT | Update settings |
| `/api/settings/mode` | PUT | Switch mode (chat/rag/search) |
| `/api/model/status` | GET | Model load status |

## WebSocket Protocol

```typescript
// Client → Server
{ type: "message", content: "Hello", conversation_id: "..." }
{ type: "cancel" }

// Server → Client
{ type: "token", content: "Hi" }
{ type: "complete", message: {...}, sources: [...] }
{ type: "error", message: "..." }
{ type: "status", generating: true }
```

## Key Dependencies

### Python (requirements.txt)
```
# API
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6
websockets>=12.0

# LLM
llama-cpp-python>=0.2.0

# RAG
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

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}
```

## Model Recommendations

| Model | Size | VRAM | Best For |
|-------|------|------|----------|
| Phi-3.5 Mini 4K Q4 | 2.4GB | 4GB | Low-end hardware (current) |
| Llama 3.2 3B Q4 | 2GB | 4GB | Good balance |
| Mistral 7B Q4 | 4GB | 8GB | Higher quality |

## Getting Started

```bash
# Backend
cd Hearth-AI
source venv/bin/activate
pip install -r requirements.txt
python src/main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev      # Development
npm run build    # Production build
```

Access at: `http://127.0.0.1:8080`

---

**Status:** Phases 1-6 complete. The FastAPI + React app is the mainline
as of the v1.0.1 merge into `main`.

Verified on Windows (Python 3.13): frontend builds, test suite passes,
`python src/main.py` serves the app, and `pyinstaller build.spec` produces a
~240MB dist/HearthAI/ whose executable starts and serves the bundled frontend
from sys._MEIPASS.

Outstanding:
- Drag-and-drop document upload (Phase 5, optional - the sidebar upload
  button works today).
- PyInstaller build unverified on Linux and macOS.
- tests/ holds a single test that makes live DuckDuckGo calls and asserts
  nothing; it detects import and crash regressions only.
