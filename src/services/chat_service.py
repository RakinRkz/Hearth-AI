"""Chat service for managing conversations and generating responses."""

from typing import Generator, List, Dict, Any, Optional, Callable
from pathlib import Path
from enum import Enum
import sys

from .llm_service import LLMService
from .rag_service import RAGService
from .search_service import SearchService

# Add parent to path for sibling imports
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from models.message import Message, MessageRole, Source
from models.conversation import Conversation


class ChatMode(Enum):
    """Chat mode options."""
    CHAT = "chat"
    RAG = "rag"
    SEARCH = "search"


class ChatService:
    """Service for managing chat conversations."""
    
    RAG_SYSTEM_TEMPLATE = """You are a helpful AI assistant. Answer the user's question based on the provided context. 
If the context doesn't contain relevant information, say so and provide a general answer if possible.
Always cite your sources using [1], [2], etc. when using information from the context.

Context:
{context}
"""
    
    SEARCH_SYSTEM_TEMPLATE = """You are a helpful AI assistant with web search results.
Answer based on the search results. Cite sources using [1], [2], etc.

Search Results:
{context}
"""
    
    def __init__(
        self,
        llm_service: LLMService,
        rag_service: Optional[RAGService] = None,
        search_service: Optional[SearchService] = None,
        conversations_dir: str = "data/conversations",
    ):
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.search_service = search_service
        self.conversations_dir = conversations_dir
        
        self.current_conversation: Optional[Conversation] = None
        self.mode: ChatMode = ChatMode.CHAT
        
        # Ensure conversations directory exists
        Path(conversations_dir).mkdir(parents=True, exist_ok=True)
    
    def new_conversation(self, system_prompt: Optional[str] = None) -> Conversation:
        """Create a new conversation."""
        self.current_conversation = Conversation(
            system_prompt=system_prompt or "You are a helpful AI assistant."
        )
        return self.current_conversation
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation by ID."""
        file_path = Path(self.conversations_dir) / f"{conversation_id}.json"
        if file_path.exists():
            self.current_conversation = Conversation.load(str(file_path))
            return self.current_conversation
        return None
    
    def save_conversation(self) -> Optional[str]:
        """Save the current conversation."""
        if self.current_conversation:
            return self.current_conversation.save(self.conversations_dir)
        return None
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all saved conversations."""
        conversations = []
        conv_path = Path(self.conversations_dir)
        
        for file in conv_path.glob("*.json"):
            try:
                conv = Conversation.load(str(file))
                conversations.append({
                    "id": conv.id,
                    "title": conv.title,
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": len(conv.messages),
                })
            except Exception:
                continue
        
        # Sort by updated_at descending
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        file_path = Path(self.conversations_dir) / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()
            if self.current_conversation and self.current_conversation.id == conversation_id:
                self.current_conversation = None
            return True
        return False
    
    def _prepare_messages(
        self, 
        user_message: str
    ) -> tuple[List[Dict[str, str]], List[Source]]:
        """Prepare messages for LLM based on current mode."""
        if not self.current_conversation:
            self.new_conversation()
        
        sources = []
        system_prompt = self.current_conversation.system_prompt
        
        # Handle RAG mode
        if self.mode == ChatMode.RAG and self.rag_service:
            context, rag_sources = self.rag_service.get_context_for_query(user_message)
            if context:
                system_prompt = self.RAG_SYSTEM_TEMPLATE.format(context=context)
                sources = [
                    Source(
                        title=s["title"],
                        content=s["content"],
                        page=s.get("page"),
                    )
                    for s in rag_sources
                ]
        
        # Handle Search mode
        elif self.mode == ChatMode.SEARCH and self.search_service:
            print(f"[DEBUG] Search mode active, searching for: {user_message}")
            context, search_sources = self.search_service.get_context_for_query(user_message)
            print(f"[DEBUG] Search returned {len(search_sources)} sources, context length: {len(context)}")
            if context:
                system_prompt = self.SEARCH_SYSTEM_TEMPLATE.format(context=context)
                sources = [
                    Source(
                        title=s["title"],
                        content=s["content"],
                        url=s.get("url"),
                    )
                    for s in search_sources
                ]
            else:
                print("[DEBUG] No search context returned!")
        
        # Build messages list
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (limit to recent messages to fit context)
        history = self.current_conversation.messages
        # Keep only last 6 messages to prevent context overflow
        if len(history) > 6:
            history = history[-6:]
        
        for msg in history:
            messages.append(msg.to_llm_format())
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        print(f"[DEBUG] Prepared {len(messages)} messages for LLM")
        print(f"[DEBUG] System prompt length: {len(system_prompt)}")
        
        return messages, sources
    
    def send_message(
        self,
        user_message: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Message:
        """Send a message and get a response (non-streaming)."""
        if not self.current_conversation:
            self.new_conversation()
        
        # Add user message to conversation
        self.current_conversation.add_message(MessageRole.USER, user_message)
        
        # Prepare messages and get context
        messages, sources = self._prepare_messages(user_message)
        
        # Generate response
        response_text = self.llm_service.generate(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        # Add assistant response to conversation
        assistant_message = self.current_conversation.add_message(
            MessageRole.ASSISTANT, 
            response_text,
            sources=sources,
        )
        
        # Auto-save
        self.save_conversation()
        
        return assistant_message
    
    def send_message_stream(
        self,
        user_message: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Generator[str, None, Message]:
        """Send a message and stream the response."""
        if not self.current_conversation:
            self.new_conversation()
        
        # Add user message to conversation
        self.current_conversation.add_message(MessageRole.USER, user_message)
        
        # Prepare messages and get context
        messages, sources = self._prepare_messages(user_message)
        
        # Stream response
        response_parts = []
        for token in self.llm_service.generate_stream(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        ):
            response_parts.append(token)
            yield token
        
        # Add complete assistant response to conversation
        response_text = "".join(response_parts)
        assistant_message = self.current_conversation.add_message(
            MessageRole.ASSISTANT,
            response_text,
            sources=sources,
        )
        
        # Auto-save
        self.save_conversation()
        
        return assistant_message
    
    def send_message_async(
        self,
        user_message: str,
        on_token: Callable[[str], None],
        on_complete: Optional[Callable[[Message], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> None:
        """Send a message asynchronously with callbacks."""
        if not self.current_conversation:
            self.new_conversation()
        
        # Add user message to conversation
        self.current_conversation.add_message(MessageRole.USER, user_message)
        
        # Prepare messages and get context
        messages, sources = self._prepare_messages(user_message)
        
        response_parts = []
        
        def _on_token(token: str):
            response_parts.append(token)
            on_token(token)
        
        def _on_complete():
            response_text = "".join(response_parts)
            assistant_message = self.current_conversation.add_message(
                MessageRole.ASSISTANT,
                response_text,
                sources=sources,
            )
            self.save_conversation()
            if on_complete:
                on_complete(assistant_message)
        
        self.llm_service.generate_async(
            messages=messages,
            callback=_on_token,
            on_complete=_on_complete,
            on_error=on_error,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    
    def set_mode(self, mode: ChatMode) -> None:
        """Set the chat mode."""
        self.mode = mode
    
    def get_mode(self) -> ChatMode:
        """Get the current chat mode."""
        return self.mode
