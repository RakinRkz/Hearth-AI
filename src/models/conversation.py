"""Conversation data model."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4

from .message import Message, MessageRole

# Single source of truth for the assistant's identity.
#
# Every line here is load-bearing and was arrived at by measurement, not taste:
#   - Naming the model to avoid ("never say you are Phi") and the vendor
#     ("created by Microsoft") is what actually suppresses the leak. Measured
#     over 16 samples on Phi-3.5, an earlier wording leaked "Microsoft" in
#     4 of them; this wording leaked in none.
#   - The no-disclaimers line exists because the previous prompt's privacy
#     sentence was being recited back as boilerplate on every reply. Stating
#     the property is fine; instructing the model to announce it is not.
DEFAULT_SYSTEM_PROMPT = (
    "You are Hearth, a helpful AI assistant running locally on the user's computer.\n\n"
    "Your name is Hearth. Never say you are Phi, and never say you were created by "
    "Microsoft or any other company.\n\n"
    "Reply directly and concisely to what the user says. Do not add disclaimers about "
    "being an AI, about privacy, or about data security unless the user asks about them."
)


@dataclass
class Conversation:
    """A conversation containing multiple messages."""
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = "New Conversation"
    messages: List[Message] = field(default_factory=list)
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: MessageRole, content: str, **kwargs) -> Message:
        """Add a message to the conversation."""
        message = Message(role=role, content=content, **kwargs)
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # Auto-generate title from first user message
        if self.title == "New Conversation" and role == MessageRole.USER:
            self.title = content[:50] + ("..." if len(content) > 50 else "")
        
        return message
    
    def get_messages_for_llm(self, include_system: bool = True) -> List[Dict[str, str]]:
        """Get messages formatted for LLM input."""
        messages = []
        
        if include_system and self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        for msg in self.messages:
            messages.append(msg.to_llm_format())
        
        return messages
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "messages": [m.to_dict() for m in self.messages],
            "system_prompt": self.system_prompt,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create conversation from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            messages=[Message.from_dict(m) for m in data["messages"]],
            system_prompt=data.get("system_prompt", DEFAULT_SYSTEM_PROMPT),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )
    
    def save(self, directory: str) -> str:
        """Save conversation to a JSON file."""
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        
        file_path = path / f"{self.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        return str(file_path)
    
    def save_context(self, directory: str) -> str:
        """Save conversation context to markdown file.
        
        This file contains the formatted context shown to the user,
        which may include summaries of old messages.
        """
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        
        context_lines = []
        
        # Add system prompt
        if self.system_prompt:
            context_lines.append("# System Prompt")
            context_lines.append(self.system_prompt)
            context_lines.append("")
            context_lines.append("---")
            context_lines.append("")
        
        # Add messages
        for msg in self.messages:
            role_header = "## User" if msg.role == MessageRole.USER else "## Assistant"
            context_lines.append(role_header)
            context_lines.append(msg.content)
            context_lines.append("")
        
        context_text = "\n".join(context_lines)
        
        context_file = path / f"{self.id}.context.md"
        with open(context_file, "w", encoding="utf-8") as f:
            f.write(context_text)
        
        return str(context_file)
    
    def load_context(self, directory: str) -> Optional[str]:
        """Load conversation context from markdown file."""
        context_file = Path(directory) / f"{self.id}.context.md"
        if context_file.exists():
            with open(context_file, "r", encoding="utf-8") as f:
                return f.read()
        return None
    
    def get_context_token_count(self, directory: str) -> int:
        """Get estimated token count of context file."""
        context = self.load_context(directory)
        if context:
            # Rough estimate: ~4 characters per token
            return len(context) // 4
        return 0
    
    @classmethod
    def load(cls, file_path: str) -> "Conversation":
        """Load conversation from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def export_markdown(self) -> str:
        """Export conversation as Markdown."""
        lines = [f"# {self.title}\n"]
        lines.append(f"*Created: {self.created_at.strftime('%Y-%m-%d %H:%M')}*\n")
        
        if self.system_prompt:
            lines.append(f"**System Prompt:** {self.system_prompt}\n")
        
        lines.append("---\n")
        
        for msg in self.messages:
            role_label = "👤 **User**" if msg.role == MessageRole.USER else "🤖 **Assistant**"
            lines.append(f"{role_label}:\n\n{msg.content}\n")
            
            if msg.sources:
                lines.append("\n*Sources:*")
                for source in msg.sources:
                    if source.url:
                        lines.append(f"- [{source.title}]({source.url})")
                    else:
                        lines.append(f"- {source.title}")
                        if source.page:
                            lines[-1] += f" (page {source.page})"
                lines.append("")
            
            lines.append("---\n")
        
        return "\n".join(lines)
