"""Service singletons and dependency injection."""

from pathlib import Path
from typing import Optional
import sys

# Add parent to path for imports
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from services.llm_service import LLMService
from services.embedding_service import EmbeddingService
from services.chat_service import ChatService, ChatMode
from services.rag_service import RAGService
from services.search_service import SearchService
from utils.config import get_config, get_config_manager

# Service singletons
_llm_service: Optional[LLMService] = None
_embedding_service: Optional[EmbeddingService] = None
_chat_service: Optional[ChatService] = None
_rag_service: Optional[RAGService] = None
_search_service: Optional[SearchService] = None


def get_llm_service() -> Optional[LLMService]:
    """Get or create LLM service singleton."""
    global _llm_service
    return _llm_service


def get_embedding_service() -> Optional[EmbeddingService]:
    """Get or create embedding service singleton."""
    global _embedding_service
    return _embedding_service


def get_chat_service() -> Optional[ChatService]:
    """Get or create chat service singleton."""
    global _chat_service
    return _chat_service


def get_rag_service() -> Optional[RAGService]:
    """Get or create RAG service singleton."""
    global _rag_service
    return _rag_service


def get_search_service() -> Optional[SearchService]:
    """Get or create search service singleton."""
    global _search_service
    return _search_service


def initialize_services(model_path: Optional[str] = None) -> dict:
    """
    Initialize all services.
    
    Args:
        model_path: Optional path to LLM model file
        
    Returns:
        Dict with initialization status
    """
    global _llm_service, _embedding_service, _chat_service, _rag_service, _search_service
    
    config = get_config()
    status = {
        "llm": False,
        "embedding": False,
        "rag": False,
        "search": False,
        "errors": []
    }
    
    # Resolve model path
    if model_path:
        resolved_model_path = model_path
    elif config.model_path:
        resolved_model_path = config.model_path
    else:
        # Try to find a model in the models directory
        models_dir = Path(__file__).parent.parent.parent / config.models_dir
        gguf_files = list(models_dir.glob("*.gguf"))
        if gguf_files:
            resolved_model_path = str(gguf_files[0])
        else:
            resolved_model_path = None
    
    # Initialize LLM Service
    if resolved_model_path and Path(resolved_model_path).exists():
        try:
            _llm_service = LLMService(
                model_path=resolved_model_path,
                context_length=config.context_length,
                gpu_layers=config.gpu_layers,
            )
            _llm_service.load_model()
            status["llm"] = True
        except Exception as e:
            status["errors"].append(f"LLM: {str(e)}")
    else:
        status["errors"].append("LLM: No model file found")
    
    # Initialize Embedding Service
    try:
        _embedding_service = EmbeddingService(model_name=config.embedding_model)
        _embedding_service.load_model()
        status["embedding"] = True
    except Exception as e:
        status["errors"].append(f"Embedding: {str(e)}")
    
    # Initialize RAG Service
    if _embedding_service and _embedding_service.is_loaded:
        try:
            data_dir = Path(__file__).parent.parent.parent / config.data_dir
            _rag_service = RAGService(
                embedding_service=_embedding_service,
                persist_directory=str(data_dir / "vectorstore"),
            )
            status["rag"] = True
        except Exception as e:
            status["errors"].append(f"RAG: {str(e)}")
    
    # Initialize Search Service
    try:
        _search_service = SearchService(max_results=config.max_search_results)
        status["search"] = True
    except Exception as e:
        status["errors"].append(f"Search: {str(e)}")
    
    # Initialize Chat Service (requires LLM)
    if _llm_service and _llm_service.is_loaded:
        try:
            data_dir = Path(__file__).parent.parent.parent / config.data_dir
            _chat_service = ChatService(
                llm_service=_llm_service,
                rag_service=_rag_service,
                search_service=_search_service,
                conversations_dir=str(data_dir / "conversations"),
            )
            status["chat"] = True
        except Exception as e:
            status["errors"].append(f"Chat: {str(e)}")
    
    return status


def shutdown_services():
    """Shutdown all services and release resources."""
    global _llm_service, _embedding_service, _chat_service, _rag_service, _search_service
    
    # Unload LLM to free VRAM
    if _llm_service:
        try:
            _llm_service.unload_model()
        except Exception:
            pass
    
    _llm_service = None
    _embedding_service = None
    _chat_service = None
    _rag_service = None
    _search_service = None


def set_chat_mode(mode: str) -> bool:
    """Set the chat mode."""
    if _chat_service:
        try:
            _chat_service.set_mode(ChatMode(mode))
            return True
        except ValueError:
            return False
    return False


def get_chat_mode() -> Optional[str]:
    """Get the current chat mode."""
    if _chat_service:
        return _chat_service.get_mode().value
    return None
