# Hearth AI - Architecture Documentation

## Overview

The Hearth AI is a **local cross-platform web-based** AI chat application with advanced capabilities including Retrieval-Augmented Generation (RAG) and web search integration. The application runs entirely locally using llama.cpp for LLM inference and provides a modern web interface accessed via browser.

### Core Features
- 💬 **Direct Chat** - Conversation with local LLM models
- 📄 **RAG (Retrieval-Augmented Generation)** - Document-based Q&A with source citations
- 🌐 **Web Search** - Real-time web search integration via DuckDuckGo
- 🔄 **Streaming Responses** - Real-time token streaming for improved UX
- 💾 **Conversation Management** - Save, load, and manage chat history
- 📁 **Document Processing** - Support for PDF, TXT, MD, and DOCX files

## High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React Frontend<br/>Vite + TypeScript + Tailwind CSS]
        CTX[React Contexts<br/>Settings, Chat, Conversations]
        COMP[UI Components<br/>ChatView, Sidebar, MessageInput]
    end
    
    subgraph "API Layer"
        WS[WebSocket<br/>/ws/chat]
        REST[REST API<br/>/api/*]
        FAST[FastAPI App<br/>CORS + Routing]
    end
    
    subgraph "Service Layer"
        CHAT[ChatService<br/>Orchestration]
        LLM[LLMService<br/>llama-cpp-python]
        RAG[RAGService<br/>Document Processing]
        SEARCH[SearchService<br/>DuckDuckGo]
        EMBED[EmbeddingService<br/>fastembed ONNX]
    end
    
    subgraph "Storage Layer"
        VECTOR[ChromaDB<br/>Vector Store]
        FILES[File System<br/>Conversations & Documents]
        CONFIG[Config JSON<br/>User Settings]
    end
    
    UI --> WS
    UI --> REST
    WS --> CHAT
    REST --> CHAT
    FAST --> WS
    FAST --> REST
    
    CHAT --> LLM
    CHAT --> RAG
    CHAT --> SEARCH
    RAG --> EMBED
    RAG --> VECTOR
    
    VECTOR --> FILES
    CONFIG --> FILES
    
    class UI,CTX,COMP frontend
    class WS,REST,FAST api
    class CHAT,LLM,RAG,SEARCH,EMBED service
    class VECTOR,FILES,CONFIG storage
```

## Detailed System Architecture

### 1. Frontend Architecture

The frontend is built with React 19, TypeScript, and Vite, providing a modern and responsive user interface.

```mermaid
graph TD
    subgraph "React Application Structure"
        APP[App.tsx<br/>Root Component + Providers]
        
        subgraph "Context Layer"
            SETTINGS_CTX[SettingsContext<br/>Mode, Theme, Config]
            CHAT_CTX[ChatContext<br/>Messages, Streaming]
            CONV_CTX[ConversationContext<br/>CRUD Operations]
        end
        
        subgraph "Page Components"
            MAIN[Main Layout<br/>Sidebar + Chat Area]
            SIDEBAR[Sidebar<br/>Navigation & Controls]
            CHAT_VIEW[ChatView<br/>Message Display]
        end
        
        subgraph "UI Components"
            MSG_BUBBLE[MessageBubble<br/>User/Assistant Messages]
            MSG_INPUT[MessageInput<br/>Text Input + Send]
            SETTINGS_DLG[SettingsDialog<br/>Configuration Modal]
            CTX_DLG[ContextDialog<br/>Document Upload]
        end
        
        subgraph "Utilities"
            API_CLIENT[API Client<br/>HTTP + WebSocket]
            TYPES[Type Definitions<br/>TypeScript Interfaces]
            UTILS[Utility Functions<br/>Formatting, Validation]
        end
    end
    
    APP --> SETTINGS_CTX
    APP --> CHAT_CTX
    APP --> CONV_CTX
    
    MAIN --> SIDEBAR
    MAIN --> CHAT_VIEW
    
    CHAT_VIEW --> MSG_BUBBLE
    CHAT_VIEW --> MSG_INPUT
    
    SIDEBAR --> SETTINGS_DLG
    SIDEBAR --> CTX_DLG
    
    CHAT_CTX --> API_CLIENT
    CONV_CTX --> API_CLIENT
    
    API_CLIENT --> TYPES
    API_CLIENT --> UTILS
    
    class SETTINGS_CTX,CHAT_CTX,CONV_CTX context
    class MAIN,SIDEBAR,CHAT_VIEW,MSG_BUBBLE,MSG_INPUT,SETTINGS_DLG,CTX_DLG component
    class API_CLIENT,TYPES,UTILS utility
```

#### Key Frontend Components

- **App.tsx**: Root component that provides React contexts and manages global state
- **ChatContext**: Manages chat messages, streaming state, and WebSocket connections
- **ConversationContext**: Handles conversation CRUD operations and persistence
- **SettingsContext**: Manages application settings, themes, and configuration
- **Sidebar**: Navigation, mode selection, conversation list, and document management
- **ChatView**: Main chat interface with message display and auto-scrolling
- **MessageBubble**: Individual message rendering with source citations
- **MessageInput**: Text input with send functionality and keyboard shortcuts

### 2. Backend API Architecture

The backend uses FastAPI to provide both REST endpoints and WebSocket connections for real-time streaming.

```mermaid
graph TB
    subgraph "FastAPI Backend"
        MAIN_API[main.py<br/>FastAPI App Setup]
        DEPS[dependencies.py<br/>Service Singletons]
        SCHEMAS[schemas.py<br/>Pydantic Models]
        
        subgraph "API Routes"
            CHAT_WS[chat.py<br/>WebSocket /ws/chat]
            CONV_REST[conversations.py<br/>/api/conversations]
            DOCS_REST[documents.py<br/>/api/documents]
            SET_REST[settings.py<br/>/api/settings]
        end
        
        subgraph "Middleware"
            CORS[CORS Middleware<br/>Cross-Origin Support]
            STATIC[Static Files<br/>Frontend Serving]
        end
    end
    
    MAIN_API --> CORS
    MAIN_API --> STATIC
    MAIN_API --> CHAT_WS
    MAIN_API --> CONV_REST
    MAIN_API --> DOCS_REST
    MAIN_API --> SET_REST
    
    CHAT_WS --> DEPS
    CONV_REST --> DEPS
    DOCS_REST --> DEPS
    SET_REST --> DEPS
    
    DEPS --> SCHEMAS
    
    class MAIN_API,DEPS,SCHEMAS api
    class CHAT_WS,CONV_REST,DOCS_REST,SET_REST route
    class CORS,STATIC middleware
```

#### API Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/ws/chat` | WebSocket | Real-time streaming chat | Token stream |
| `/api/conversations` | GET | List all conversations | Array of conversations |
| `/api/conversations` | POST | Create new conversation | Created conversation |
| `/api/conversations/{id}` | GET | Load specific conversation | Conversation details |
| `/api/conversations/{id}` | DELETE | Delete conversation | Success status |
| `/api/documents` | GET | List uploaded documents | Array of documents |
| `/api/documents` | POST | Upload document | Upload status |
| `/api/documents/{id}` | DELETE | Delete document | Success status |
| `/api/settings` | GET | Get current settings | Configuration object |
| `/api/settings` | PUT | Update settings | Updated configuration |
| `/api/model/status` | GET | Model loading status | Status object |

#### WebSocket Protocol

```mermaid
sequenceDiagram
    participant Client
    participant WebSocket
    participant ChatService
    participant LLMService
    
    Client->>WebSocket: Connect to /ws/chat
    Client->>WebSocket: {"type": "message", "content": "Hello", "conversation_id": "..."}
    WebSocket->>ChatService: Process message
    ChatService->>LLMService: Generate response (streaming)
    
    loop Token Streaming
        LLMService->>ChatService: Token
        ChatService->>WebSocket: {"type": "token", "content": "Hi"}
        WebSocket->>Client: Stream token
    end
    
    LLMService->>ChatService: Complete
    ChatService->>WebSocket: {"type": "complete", "message": {...}, "sources": [...]}
    WebSocket->>Client: Completion notice
    
    Note over Client,LLMService: Client can send {"type": "cancel"} at any time
```

### 3. Service Layer Architecture

The service layer implements the core business logic and orchestrates different AI capabilities.

```mermaid
graph TD
    subgraph "Service Architecture"
        subgraph "Core Orchestration"
            CHAT_SVC[ChatService<br/>Main Controller]
        end
        
        subgraph "AI Services"
            LLM_SVC[LLMService<br/>llama-cpp-python]
            EMBED_SVC[EmbeddingService<br/>fastembed ONNX]
        end
        
        subgraph "Feature Services"
            RAG_SVC[RAGService<br/>Document Processing]
            SEARCH_SVC[SearchService<br/>Web Search]
        end
        
        subgraph "Processing Modes"
            CHAT_MODE[Chat Mode<br/>Direct LLM]
            RAG_MODE[RAG Mode<br/>Document Context]
            SEARCH_MODE[Search Mode<br/>Web Context]
        end
        
        subgraph "External Integrations"
            LLAMA[llama-cpp-python<br/>Local LLM Inference]
            CHROMA[ChromaDB<br/>Vector Database]
            DDGS[DuckDuckGo<br/>Web Search API]
            FASTEMBED[fastembed<br/>ONNX Embeddings]
        end
    end
    
    CHAT_SVC --> LLM_SVC
    CHAT_SVC --> RAG_SVC
    CHAT_SVC --> SEARCH_SVC
    
    LLM_SVC --> LLAMA
    EMBED_SVC --> FASTEMBED
    RAG_SVC --> EMBED_SVC
    RAG_SVC --> CHROMA
    SEARCH_SVC --> DDGS
    
    CHAT_SVC --> CHAT_MODE
    CHAT_SVC --> RAG_MODE
    CHAT_SVC --> SEARCH_MODE
    
    class CHAT_SVC orchestration
    class LLM_SVC,EMBED_SVC ai
    class RAG_SVC,SEARCH_SVC feature
    class CHAT_MODE,RAG_MODE,SEARCH_MODE mode
    class LLAMA,CHROMA,DDGS,FASTEMBED external
```

#### Service Descriptions

##### ChatService
- **Purpose**: Main orchestrator that coordinates all other services
- **Modes**: Handles three operation modes (Chat, RAG, Search)
- **Responsibilities**: 
  - Message processing and routing
  - Context injection for RAG/Search modes
  - Conversation management and persistence
  - Streaming response coordination

##### LLMService
- **Purpose**: Wraps llama-cpp-python for local LLM inference
- **Features**: 
  - Model loading and unloading
  - Synchronous and asynchronous generation
  - Streaming token generation with callbacks
  - GPU acceleration support (CUDA/Metal)
- **Configuration**: Context length, GPU layers, sampling parameters

##### EmbeddingService
- **Purpose**: Text embedding generation using ONNX models
- **Technology**: fastembed (avoids CUDA conflicts with llama-cpp-python)
- **Models**: Uses optimized ONNX models like all-MiniLM-L6-v2
- **Benefits**: Fast inference, CPU-optimized, small memory footprint

##### RAGService
- **Purpose**: Document processing and retrieval for Q&A
- **Components**:
  - Document loading (PDF, TXT, MD, DOCX)
  - Text chunking with overlap
  - Vector storage using ChromaDB
  - Similarity search and ranking
- **Features**: Source citation, relevance scoring, document management

##### SearchService
- **Purpose**: Web search integration for real-time information
- **Provider**: DuckDuckGo (no API key required)
- **Features**: Query processing, result ranking, snippet extraction

### 4. Data Flow Architecture

The Hearth AI implements three distinct data processing pipelines, each optimized for different use cases and information sources.

```mermaid
flowchart TD
    subgraph "💬 Chat Mode: Direct LLM Conversation"
        U1[👤 User Message] --> C1{ChatService<br/>Route & Validate}
        C1 --> P1[📝 Prepare Prompt<br/>+ System Context]
        P1 --> L1[🤖 LLM Inference<br/>llama-cpp-python]
        L1 --> S1[📡 Stream Tokens<br/>WebSocket]
        S1 --> R1[✅ Response<br/>Complete]
        
    end
```

```mermaid
flowchart TD
    subgraph "📄 RAG Mode: Document-Enhanced Q&A"
        U2[👤 User Question] --> C2{ChatService<br/>Route to RAG}
        C2 --> R2[🔍 RAGService<br/>Process Query]
        R2 --> E2[🧮 EmbeddingService<br/>Encode Query]
        E2 --> V2[📊 Vector Search<br/>ChromaDB Similarity]
        V2 --> D2[📑 Document Chunks<br/>Top-K Results]
        D2 --> X2[🔗 Context Assembly<br/>+ Source Metadata]
        X2 --> L2[🤖 LLM + Context<br/>Enhanced Generation]
        L2 --> S2[📡 Stream Response<br/>+ Citations]
        S2 --> R2_OUT[✅ Response + Sources<br/>Complete]
        
    end

```

```mermaid
flowchart TD
    
    subgraph "🌐 Search Mode: Real-time Web Information"
        U3[👤 Search Query] --> C3{ChatService<br/>Route to Search}
        C3 --> S3[🔍 SearchService<br/>Query Processing]
        S3 --> D3[🦆 DuckDuckGo API<br/>Web Search]
        D3 --> W3[📰 Search Results<br/>Title + Snippet + URL]
        W3 --> F3[🧹 Filter & Rank<br/>Relevance Scoring]
        F3 --> X3[🔗 Context Formation<br/>Structured Summary]
        X3 --> L3[🤖 LLM + Web Context<br/>Informed Response]
        L3 --> S3_OUT[📡 Stream Response<br/>+ Web Sources]
        S3_OUT --> R3[✅ Response + Links<br/>Complete]
        
    end
```

#### Data Flow Explanations

##### 💬 **Chat Mode Flow**
1. **User Input**: Direct message from user interface
2. **Routing**: ChatService validates and routes to direct LLM processing
3. **Prompt Preparation**: System prompt + user message formatting
4. **LLM Inference**: Local model generates response using llama-cpp-python
5. **Streaming**: Tokens streamed in real-time via WebSocket
6. **Completion**: Full response delivered to user

##### 📄 **RAG Mode Flow**
1. **User Question**: Question about uploaded documents
2. **RAG Routing**: ChatService directs to RAG pipeline
3. **Query Embedding**: User question converted to vector representation
4. **Vector Search**: Similarity search against document embeddings in ChromaDB
5. **Chunk Retrieval**: Most relevant document sections retrieved
6. **Context Assembly**: Retrieved chunks formatted with source metadata
7. **Enhanced Generation**: LLM generates response using document context
8. **Cited Response**: Answer includes source citations and references

##### 🌐 **Search Mode Flow**
1. **Search Query**: User's request for current/web information
2. **Search Routing**: ChatService activates web search pipeline
3. **Query Processing**: Search terms optimized for web search
4. **Web Search**: DuckDuckGo API returns relevant web results
5. **Result Processing**: Results filtered, ranked, and summarized
6. **Context Formation**: Web content structured for LLM consumption
7. **Informed Generation**: LLM responds using current web information
8. **Sourced Response**: Answer includes web links and source attribution

#### Key Data Flow Characteristics

| Mode | Latency | Context Source | Response Type | Use Case |
|------|---------|---------------|---------------|----------|
| **Chat** | ~2-5s | System Prompt | Direct Answer | General conversation, coding help |
| **RAG** | ~3-8s | Documents | Cited Answer | Document Q&A, research queries |
| **Search** | ~5-10s | Web Results | Sourced Answer | Current events, real-time info |

### 5. Data Models and Storage

```mermaid
classDiagram
    class Message {
        +MessageRole role
        +String content
        +DateTime timestamp
        +List~Source~ sources
        +Dict metadata
        +to_dict()
        +from_dict()
    }
    
    class Conversation {
        +String id
        +String title
        +List~Message~ messages
        +String system_prompt
        +DateTime created_at
        +DateTime updated_at
        +save()
        +load()
        +export_markdown()
        +add_message()
    }
    
    class Source {
        +String title
        +String content
        +String url
        +Int page
        +Float score
    }
    
    class AppConfig {
        +String models_dir
        +String data_dir
        +String model_path
        +Int context_length
        +Int max_tokens
        +Float temperature
        +Int gpu_layers
        +save()
        +load()
    }
    
    Message "1..*" --> "0..*" Source
    Conversation "1" --> "*" Message
    
    classDef model fill:#e8f5e8
    classDef config fill:#f3e5f5
    
    class Message model
    class Conversation model
    class Source model
    class AppConfig config
```

#### Storage Structure

```
data/
├── config.json                 # Application configuration
├── conversations/             
│   ├── {uuid}.json           # Individual conversation files
│   └── metadata.json         # Conversation metadata
├── vectorstore/              # ChromaDB persistence
│   ├── chroma.sqlite3        # Vector database
│   └── indexed_files.json    # Document indexing metadata
└── logs/                     # Application logs (optional)
```

### 6. Configuration Management

The application uses a hierarchical configuration system:

```mermaid
graph TD
    subgraph "Configuration Hierarchy"
        DEFAULT[Default Config<br/>Hardcoded Defaults]
        ENV[Environment Variables<br/>Development Overrides]
        FILE[Config File<br/>data/config.json]
        UI[UI Settings<br/>Runtime Changes]
    end
    
    DEFAULT --> ENV
    ENV --> FILE
    FILE --> UI
    
    subgraph "Configuration Categories"
        LLM_CONFIG[LLM Settings<br/>Model, Context, GPU]
        RAG_CONFIG[RAG Settings<br/>Chunking, Retrieval]
        UI_CONFIG[UI Settings<br/>Theme, Layout]
        PATH_CONFIG[Path Settings<br/>Models, Data, Documents]
    end
    
    UI --> LLM_CONFIG
    UI --> RAG_CONFIG
    UI --> UI_CONFIG
    UI --> PATH_CONFIG
    
    class DEFAULT,ENV,FILE,UI hierarchy
    class LLM_CONFIG,RAG_CONFIG,UI_CONFIG,PATH_CONFIG category
```

### 7. Deployment Architecture

```mermaid
graph TB
    subgraph "Production Deployment"
        subgraph "Single Process"
            UVICORN[Uvicorn Server<br/>Port 8080]
            STATIC_SERVE[Static File Serving<br/>Frontend Assets]
            API_SERVE[API Endpoints<br/>REST + WebSocket]
        end
        
        subgraph "File System"
            MODELS_DIR[models/<br/>GGUF Files]
            DATA_DIR[data/<br/>User Data]
            DOCS_DIR[documents/<br/>Uploaded Files]
        end
        
        subgraph "Browser Access"
            BROWSER[Web Browser<br/>http://localhost:8080]
        end
    end
    
    BROWSER --> UVICORN
    UVICORN --> STATIC_SERVE
    UVICORN --> API_SERVE
    
    API_SERVE --> MODELS_DIR
    API_SERVE --> DATA_DIR
    API_SERVE --> DOCS_DIR
    
    class UVICORN,STATIC_SERVE,API_SERVE server
    class MODELS_DIR,DATA_DIR,DOCS_DIR storage
    class BROWSER client
```

### 8. Technology Stack Details

#### Frontend Stack
- **React 19**: Modern React with concurrent features and Suspense
- **TypeScript**: Type safety and enhanced developer experience
- **Vite**: Fast build tool with HMR for development
- **Tailwind CSS v4**: Utility-first CSS framework
- **Lucide React**: Icon library for consistent UI
- **Native WebSocket API**: For real-time streaming communication

#### Backend Stack
- **FastAPI**: High-performance async web framework
- **Uvicorn**: ASGI server with WebSocket support
- **Pydantic**: Data validation and settings management
- **Python 3.11+**: Modern Python with performance improvements

#### AI/ML Stack
- **llama-cpp-python**: LLM inference with GGUF model support
- **fastembed**: ONNX-based embedding models (CPU optimized)
- **ChromaDB**: Vector database for document embeddings
- **DuckDuckGo Search**: Web search without API keys

#### Document Processing
- **PyPDF**: PDF document parsing
- **python-docx**: Word document processing
- **Built-in parsers**: TXT and Markdown support

### 9. Performance Considerations

#### Memory Management
- **Model Loading**: Lazy loading of services to minimize startup memory
- **GPU Memory**: Configurable GPU layer allocation for VRAM optimization
- **Document Chunking**: Efficient text splitting with overlap management
- **Vector Storage**: ChromaDB with configurable persistence

#### Streaming Performance
- **WebSocket Streaming**: Real-time token streaming for responsive UX
- **Async Processing**: Non-blocking LLM inference with callback handling
- **Background Tasks**: Async document processing and indexing

#### Scalability
- **Single User Design**: Optimized for local desktop usage
- **Resource Limits**: Configurable context length and batch sizes
- **Efficient Storage**: Compressed vector embeddings and conversation serialization

### 10. Security and Privacy

#### Local-First Architecture
- **No External APIs**: All processing happens locally (except optional web search)
- **Data Privacy**: Conversations and documents never leave the local machine
- **Model Privacy**: Local LLM inference without cloud dependencies

#### File Security
- **Sandboxed Upload**: Document uploads restricted to designated directories
- **Input Validation**: All user inputs validated through Pydantic schemas
- **Path Traversal Protection**: Secure file path handling

### 11. Extension and Customization

#### Adding New Document Formats
```python
# In utils/document_loader.py
def _load_new_format(self, file_path: str) -> List[DocumentChunk]:
    # Custom document parsing logic
    pass
```

#### Adding New Chat Modes
```python
# In services/chat_service.py
class ChatMode(Enum):
    CUSTOM = "custom"

# Add mode handling in ChatService._prepare_messages()
```

#### Custom LLM Integration
```python
# In services/llm_service.py
class CustomLLMService(LLMService):
    # Override methods for custom LLM integration
    pass
```

This architecture provides a robust foundation for a local AI chat application with clear separation of concerns, extensible design, and optimal performance for desktop usage.
