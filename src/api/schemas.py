"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from models.conversation import DEFAULT_SYSTEM_PROMPT


class ChatMode(str, Enum):
    """Chat mode options."""
    CHAT = "chat"
    RAG = "rag"
    SEARCH = "search"


# ============== Message Schemas ==============

class SourceSchema(BaseModel):
    """Source reference for RAG or web search."""
    title: str
    content: str
    url: Optional[str] = None
    page: Optional[int] = None


class MessageSchema(BaseModel):
    """Chat message schema."""
    role: str
    content: str
    timestamp: datetime
    sources: List[SourceSchema] = []
    metadata: Dict[str, Any] = {}


class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    content: str
    conversation_id: Optional[str] = None


# ============== Conversation Schemas ==============

class ConversationSummary(BaseModel):
    """Summary of a conversation for listing."""
    id: str
    title: str
    updated_at: datetime
    message_count: int


class ConversationDetail(BaseModel):
    """Full conversation detail."""
    id: str
    title: str
    messages: List[MessageSchema]
    system_prompt: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    title: Optional[str] = "New Conversation"
    system_prompt: Optional[str] = DEFAULT_SYSTEM_PROMPT


# ============== Document Schemas ==============

class DocumentInfo(BaseModel):
    """Information about an indexed document."""
    id: str
    filename: str
    file_path: str
    chunk_count: int
    indexed_at: datetime


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    success: bool
    filename: str
    chunk_count: int
    message: str


# ============== Settings Schemas ==============

class SettingsSchema(BaseModel):
    """Application settings."""
    # Mode
    mode: ChatMode = ChatMode.CHAT
    
    # LLM Settings
    model_path: Optional[str] = None
    context_length: int = 2048
    max_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    gpu_layers: int = -1
    
    # Embedding Settings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # RAG Settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 4
    
    # Search Settings
    search_enabled: bool = True
    max_search_results: int = 5
    
    # UI Settings
    theme: str = "dark"


class SettingsUpdate(BaseModel):
    """Schema for updating settings."""
    # All fields optional for partial updates
    mode: Optional[ChatMode] = None
    model_path: Optional[str] = None
    context_length: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repeat_penalty: Optional[float] = None
    gpu_layers: Optional[int] = None
    embedding_model: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    top_k_results: Optional[int] = None
    search_enabled: Optional[bool] = None
    max_search_results: Optional[int] = None
    theme: Optional[str] = None


class ModeUpdate(BaseModel):
    """Schema for changing chat mode."""
    mode: ChatMode


# ============== WebSocket Schemas ==============

class WSMessageIn(BaseModel):
    """Incoming WebSocket message from client."""
    type: str  # "message" or "cancel"
    content: Optional[str] = None
    conversation_id: Optional[str] = None


class WSMessageOut(BaseModel):
    """Outgoing WebSocket message to client."""
    type: str  # "token", "complete", "error", "status"
    content: Optional[str] = None
    message: Optional[MessageSchema] = None
    sources: Optional[List[SourceSchema]] = None
    generating: Optional[bool] = None
