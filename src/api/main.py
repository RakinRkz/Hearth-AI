"""FastAPI application setup."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys

# Add parent to path for imports
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from api.routes import chat, conversations, documents, settings
from utils import paths

# Create FastAPI app
app = FastAPI(
    title="Hearth AI API",
    description="Hearth AI - local AI assistant with RAG and web search",
    version="1.0.0",
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, tags=["chat"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/model/status")
async def model_status():
    """Get model load status."""
    from api.dependencies import get_llm_service, is_model_needed
    
    llm_service = get_llm_service()
    return {
        "loaded": llm_service.is_loaded if llm_service else False,
        "model_path": llm_service.model_path if llm_service else None,
        "generating": llm_service._is_generating if llm_service else False,
        "needs_download": is_model_needed(),
    }


def mount_static_files(app: FastAPI, frontend_dist: str = "frontend/dist"):
    """Mount static files for production build."""
    dist_path = paths.frontend_dist_dir()
    if dist_path.exists():
        app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")
