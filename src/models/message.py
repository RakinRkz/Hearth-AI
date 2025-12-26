"""Message data model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class MessageRole(Enum):
    """Role of a message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Source:
    """A source reference for RAG or web search results."""
    title: str
    content: str
    url: Optional[str] = None
    page: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "page": self.page
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Source":
        return cls(**data)


@dataclass
class Message:
    """A chat message."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    sources: List[Source] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "sources": [s.to_dict() for s in self.sources],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            sources=[Source.from_dict(s) for s in data.get("sources", [])],
            metadata=data.get("metadata", {})
        )
    
    def to_llm_format(self) -> Dict[str, str]:
        """Convert to format expected by LLM."""
        return {
            "role": self.role.value,
            "content": self.content
        }
