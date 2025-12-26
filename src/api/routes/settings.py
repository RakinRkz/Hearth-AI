"""REST endpoints for settings management."""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import sys

# Add parent to path for imports
src_dir = Path(__file__).parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from api.schemas import SettingsSchema, SettingsUpdate, ModeUpdate, ChatMode
from api.dependencies import get_chat_mode, set_chat_mode
from utils.config import get_config, get_config_manager

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
