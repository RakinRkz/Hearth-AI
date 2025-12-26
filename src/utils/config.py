"""Application configuration management."""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


# Default model for first-run setup
DEFAULT_MODEL_FILENAME = "Phi-3.5-mini-instruct-Q4_K_M.gguf"


@dataclass
class AppConfig:
    """Application configuration."""
    
    # Paths
    models_dir: str = "models"
    data_dir: str = "data"
    documents_dir: str = "documents"
    
    # LLM Settings
    model_path: Optional[str] = None
    context_length: int = 2048  # Reduced for 4GB VRAM GPUs
    max_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    gpu_layers: int = -1  # -1 = all layers on GPU (auto), 0 = CPU only
    
    # Embedding Settings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # RAG Settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 4
    
    # Web Search Settings
    search_enabled: bool = True
    max_search_results: int = 5
    
    # UI Settings
    theme: str = "dark"  # "dark", "light", "system"
    window_width: int = 1200
    window_height: int = 800
    
    # First run flag
    first_run: bool = True


class ConfigManager:
    """Manages application configuration persistence."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or self._get_default_config_path())
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        # Use app directory for config
        app_dir = Path(__file__).parent.parent.parent
        return app_dir / "data" / "config.json"
    
    def _load_config(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                return AppConfig(**data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Could not load config, using defaults: {e}")
                return AppConfig()
        return AppConfig()
    
    def save(self) -> None:
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(asdict(self.config), f, indent=2)
    
    def update(self, **kwargs) -> None:
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save()


# Global config instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> AppConfig:
    """Get the application configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config


def get_config_manager() -> ConfigManager:
    """Get the configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
