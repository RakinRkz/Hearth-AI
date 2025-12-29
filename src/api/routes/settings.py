"""REST endpoints for settings management."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pathlib import Path
import sys
import asyncio
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

# Add parent to path for imports
src_dir = Path(__file__).parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from api.schemas import SettingsSchema, SettingsUpdate, ModeUpdate, ChatMode
from api.dependencies import get_chat_mode, set_chat_mode, initialize_llm_service
from utils.config import get_config, get_config_manager
from utils.model_downloader import get_model_downloader, RECOMMENDED_MODELS

router = APIRouter()


# ============== Download State Tracking ==============

@dataclass
class DownloadState:
    """Tracks model download progress."""
    is_downloading: bool = False
    model_name: str = ""
    filename: str = ""
    bytes_downloaded: int = 0
    total_bytes: int = 0
    progress_percent: float = 0.0
    status: str = "idle"  # idle, downloading, completed, error
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# Global download state
_download_state = DownloadState()


def get_download_state() -> DownloadState:
    """Get current download state."""
    return _download_state


def reset_download_state():
    """Reset download state to idle."""
    global _download_state
    _download_state = DownloadState()

router = APIRouter()


@router.get("", response_model=SettingsSchema)
async def get_settings():
    """Get current application settings."""
    config = get_config()
    current_mode = get_chat_mode() or "chat"
    
    return SettingsSchema(
        mode=ChatMode(current_mode),
        model_path=config.model_path,
        context_length=config.context_length,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        top_p=config.top_p,
        top_k=config.top_k,
        repeat_penalty=config.repeat_penalty,
        gpu_layers=config.gpu_layers,
        embedding_model=config.embedding_model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        top_k_results=config.top_k_results,
        search_enabled=config.search_enabled,
        max_search_results=config.max_search_results,
        theme=config.theme,
    )


@router.put("", response_model=SettingsSchema)
async def update_settings(settings: SettingsUpdate):
    """Update application settings."""
    config_manager = get_config_manager()
    
    # Update only provided fields
    update_data = settings.model_dump(exclude_none=True)
    
    # Handle mode separately
    if "mode" in update_data:
        mode = update_data.pop("mode")
        if not set_chat_mode(mode):
            raise HTTPException(status_code=400, detail="Failed to set chat mode")
    
    # Update config
    if update_data:
        config_manager.update(**update_data)
    
    # Return updated settings
    return await get_settings()


@router.put("/mode", response_model=SettingsSchema)
async def update_mode(mode_update: ModeUpdate):
    """Switch chat mode."""
    success = set_chat_mode(mode_update.mode.value)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set chat mode")
    
    return await get_settings()


@router.get("/models")
async def list_models():
    """List available models in the models directory."""
    config = get_config()
    models_dir = Path(__file__).parent.parent.parent.parent / config.models_dir
    
    models = []
    if models_dir.exists():
        for file_path in models_dir.glob("*.gguf"):
            models.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size_mb": round(file_path.stat().st_size / (1024 * 1024), 1),
            })
    
    return {"models": models}


# ============== Model Download Endpoints ==============

@router.get("/download/status")
async def get_model_download_status():
    """Get current model download status."""
    state = get_download_state()
    return {
        "is_downloading": state.is_downloading,
        "model_name": state.model_name,
        "filename": state.filename,
        "bytes_downloaded": state.bytes_downloaded,
        "total_bytes": state.total_bytes,
        "progress_percent": state.progress_percent,
        "status": state.status,
        "error": state.error,
        "started_at": state.started_at,
        "completed_at": state.completed_at,
    }


@router.get("/download/models")
async def get_available_models():
    """Get list of recommended models available for download."""
    return {
        "models": [
            {
                "name": m.name,
                "filename": m.filename,
                "size_mb": m.size_mb,
                "description": m.description,
                "recommended": m.recommended,
            }
            for m in RECOMMENDED_MODELS
        ]
    }


@router.post("/download/start")
async def start_model_download(filename: Optional[str] = None):
    """
    Start downloading a model.
    
    Args:
        filename: Specific model filename to download, or None for default model
    """
    global _download_state
    
    if _download_state.is_downloading:
        raise HTTPException(status_code=400, detail="Download already in progress")
    
    downloader = get_model_downloader()
    
    # Find the model to download
    if filename:
        model = next((m for m in RECOMMENDED_MODELS if m.filename == filename), None)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {filename} not found")
    else:
        model = downloader.get_default_model()
    
    # Check if already installed
    if downloader.is_model_installed(model.filename):
        return {
            "status": "already_installed",
            "model_path": downloader.get_model_path(model.filename),
            "message": f"Model {model.name} is already installed"
        }
    
    # Initialize download state
    _download_state = DownloadState(
        is_downloading=True,
        model_name=model.name,
        filename=model.filename,
        total_bytes=model.size_mb * 1024 * 1024,
        status="downloading",
        started_at=datetime.now().isoformat(),
    )
    
    def on_progress(downloaded: int, total: int):
        global _download_state
        _download_state.bytes_downloaded = downloaded
        _download_state.total_bytes = total if total > 0 else model.size_mb * 1024 * 1024
        if total > 0:
            _download_state.progress_percent = round((downloaded / total) * 100, 1)
    
    def on_complete(model_path: str):
        global _download_state
        _download_state.is_downloading = False
        _download_state.status = "completed"
        _download_state.progress_percent = 100.0
        _download_state.completed_at = datetime.now().isoformat()
        print(f"✓ Model downloaded: {model_path}")
        
        # Auto-load the model
        try:
            success = initialize_llm_service(model_path)
            if success:
                print("✓ Model loaded successfully")
            else:
                print("⚠ Model downloaded but failed to load automatically")
                _download_state.error = "Model downloaded but failed to load. Please restart the application."
        except Exception as e:
            print(f"⚠ Failed to auto-load model: {e}")
            _download_state.error = f"Model downloaded but failed to load: {str(e)}"
    
    def on_error(error: str):
        global _download_state
        _download_state.is_downloading = False
        _download_state.status = "error"
        _download_state.error = error
        print(f"✗ Download error: {error}")
    
    # Start download in background
    downloader.download_model(
        model=model,
        progress_callback=on_progress,
        complete_callback=on_complete,
        error_callback=on_error,
    )
    
    return {
        "status": "started",
        "model_name": model.name,
        "filename": model.filename,
        "size_mb": model.size_mb,
        "message": f"Started downloading {model.name}"
    }


@router.post("/download/cancel")
async def cancel_model_download():
    """Cancel current model download."""
    global _download_state
    
    if not _download_state.is_downloading:
        return {"status": "not_downloading", "message": "No download in progress"}
    
    downloader = get_model_downloader()
    downloader.cancel_download()
    
    _download_state.is_downloading = False
    _download_state.status = "cancelled"
    _download_state.error = "Download cancelled by user"
    
    return {"status": "cancelled", "message": "Download cancelled"}


@router.post("/reload")
async def reload_services():
    """
    Reload/reinitialize services after model download.
    This attempts to load any available model and initialize all services.
    """
    from api.dependencies import initialize_services, get_llm_service, get_chat_service
    
    # Find the downloaded model
    config = get_config()
    models_dir = Path(__file__).parent.parent.parent.parent / config.models_dir
    gguf_files = list(models_dir.glob("*.gguf"))
    
    if not gguf_files:
        raise HTTPException(status_code=404, detail="No model files found")
    
    # Use the first available model
    model_path = str(gguf_files[0])
    
    # Reinitialize services
    status = initialize_services(model_path=model_path)
    
    llm_service = get_llm_service()
    chat_service = get_chat_service()
    
    return {
        "success": status.get("llm", False) and status.get("chat", False),
        "status": status,
        "model_loaded": llm_service.is_loaded if llm_service else False,
        "chat_ready": chat_service is not None,
        "model_path": model_path,
    }


@router.post("/models/switch")
async def switch_model(model_path: str):
    """
    Switch to a different model.
    
    Args:
        model_path: Full path to the model file to load
    """
    from api.dependencies import initialize_llm_service, get_llm_service
    
    # Validate model exists
    path = Path(model_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Model file not found: {model_path}")
    
    if not path.suffix == ".gguf":
        raise HTTPException(status_code=400, detail="Invalid model file format. Must be .gguf")
    
    # Initialize with new model
    try:
        success = initialize_llm_service(str(path))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to load model")
        
        # Update config
        config_manager = get_config_manager()
        config_manager.update(model_path=str(path))
        
        llm_service = get_llm_service()
        
        return {
            "success": True,
            "model_path": str(path),
            "model_name": path.name,
            "loaded": llm_service.is_loaded if llm_service else False,
            "message": f"Successfully switched to {path.name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")
