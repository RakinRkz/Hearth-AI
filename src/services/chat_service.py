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
from models.conversation import Conversation, DEFAULT_SYSTEM_PROMPT


class ChatMode(Enum):
    """Chat mode options."""
    CHAT = "chat"
    RAG = "rag"
    SEARCH = "search"


class ChatService:
    """Service for managing chat conversations."""
    
    RAG_SYSTEM_TEMPLATE = """You are Hearth, a helpful AI assistant with access to relevant document content.

Your task is to answer the user's question based on the document content provided below. The content comes from documents that have been analyzed and matched to the query.

IMPORTANT INSTRUCTIONS:
1. Answer the question directly using the provided document content
2. Always cite your sources using [1], [2], etc. when referring to document content
3. If the context directly answers the question, provide the answer confidently
4. If the context doesn't contain relevant information, clearly state that and provide what general help you can
5. Be specific and include details from the documents

Document Content:
{context}

Now answer the user's question using the information above:"""
    
    SEARCH_SYSTEM_TEMPLATE = """You are Hearth, a helpful AI assistant with access to current web search results.

Your task is to answer the user's question using the search results provided below. The search results include the actual content from web pages, not just snippets.

IMPORTANT INSTRUCTIONS:
1. Use the fetched content to directly answer factual questions (dates, statistics, current information, etc.)
2. When you find relevant information in the search results, cite it using [1], [2], etc.
3. If the search results contain the answer to the question, provide it directly and confidently
4. Include specific details (dates, numbers, facts) found in the search results
5. If information conflicts across sources, mention both and cite both sources
6. Only say you don't have information if it's truly not in the search results provided
7. If the search results are irrelevant to what the user actually said - for example
   they greeted you or made small talk - ignore the results completely, do not cite
   them, and just reply naturally. Never analyse or describe the search results
   themselves.

Search Results:
{context}

Now answer the user's question using the information above:"""
    
    # NO_SEARCH_SENTINEL is what the optimizer returns when the message is not a
    # search at all. Kept short and uppercase so a small model reproduces it exactly.
    NO_SEARCH_SENTINEL = "NONE"

    SEARCH_QUERY_OPTIMIZATION_PROMPT = """Extract optimal web search keywords from the user's message.
Return ONLY the search keywords, nothing else. Be concise (3-7 words).
Remove filler words. Focus on key terms that will get relevant search results.

If the message does not need a web search at all - a greeting, small talk, thanks,
or a question about you rather than about the world - return exactly NONE.

Examples:
User: "What's the latest news about Tesla's stock price and how it's been performing?"
Search: Tesla stock price news 2026

User: "Can you tell me what happened in the recent earthquake in Japan?"
Search: Japan earthquake recent news

User: "Who won the Super Bowl this year and what was the final score?"
Search: Super Bowl 2026 winner final score

User: "Hi"
Search: NONE

User: "thanks, that was helpful!"
Search: NONE

User: "who are you?"
Search: NONE

User: "{question}"
Search:"""
    
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
            system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT
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
            self.current_conversation.save(self.conversations_dir)
            # Also save context file
            self.current_conversation.save_context(self.conversations_dir)
            return self.current_conversation.id
        return None
    
    def get_context_usage(self) -> Dict[str, Any]:
        """Get current context usage metrics."""
        if not self.current_conversation:
            return {"usage_percent": 0, "token_count": 0, "max_tokens": 8000, "needs_summary": False}
        
        token_count = self.current_conversation.get_context_token_count(self.conversations_dir)
        max_tokens = 8000  # Typical context window
        usage_percent = (token_count / max_tokens) * 100
        needs_summary = usage_percent > 70
        
        return {
            "usage_percent": round(usage_percent, 1),
            "token_count": token_count,
            "max_tokens": max_tokens,
            "needs_summary": needs_summary
        }
    
    def get_safe_max_tokens(self, requested_max_tokens: int) -> int:
        """Calculate safe max_tokens based on remaining context window.
        
        Ensures the response won't exceed the context window by:
        1. Reserving space for current context usage
        2. Leaving 10% buffer for prompt overhead
        3. Clamping to valid range
        
        Args:
            requested_max_tokens: User-requested max tokens
            
        Returns:
            Safe max_tokens value that fits in context window
        """
        if not self.current_conversation:
            return max(128, min(requested_max_tokens, 4096))
        
        # The real window, not a guess. This was hardcoded to 8000 while the
        # configured default is 2048, so the calculation believed it had four
        # times the room it actually had and would approve a response that
        # overflows the context.
        context_window = self.llm_service.context_length if self.llm_service else 2048
        current_tokens = self.current_conversation.get_context_token_count(self.conversations_dir)
        
        # Reserve 10% buffer for prompt overhead and safety margin
        reserved_tokens = int(context_window * 0.10)
        available_tokens = context_window - current_tokens - reserved_tokens
        
        # Don't let response exceed available space
        safe_max = min(requested_max_tokens, max(available_tokens, 128))
        
        # Clamp to reasonable range
        return max(128, min(safe_max, 4096))
    
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
    
    def _optimize_search_query(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
        """Use LLM to extract optimal search keywords from conversation context.

        Returns None when the message does not warrant a web search at all - a
        greeting, small talk, or a question about the assistant itself. Callers
        must treat None as "answer directly, do not search".
        """
        if not self.llm_service or not self.llm_service.is_loaded:
            print("[DEBUG] LLM not available, using original query")
            return user_message
        
        try:
            # Build context from conversation history if available
            context_text = ""
            if conversation_history and len(conversation_history) > 1:
                # Include last few exchanges for context (excluding current user message)
                recent_history = conversation_history[-6:]  # Last 3 exchanges
                context_parts = []
                for msg in recent_history:
                    role = "Human" if msg["role"] == "user" else "Assistant"
                    context_parts.append(f"{role}: {msg['content'][:200]}...")  # Truncate for brevity
                context_text = f"Conversation context:\n" + "\n".join(context_parts) + f"\n\nCurrent question: {user_message}"
            else:
                context_text = user_message
            
            prompt = self.SEARCH_QUERY_OPTIMIZATION_PROMPT.format(question=context_text)
            
            # Format as chat messages for the LLM
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # Quick generation with low max_tokens for speed
            result = self.llm_service.generate(
                messages=messages,
                max_tokens=30,
                temperature=0.1,  # Low temp for consistent output
                stop=["\n", "User:", "Search:"],
            )
            
            optimized = result.strip()

            # The model may wrap the sentinel in punctuation or a short sentence;
            # treat any response that is essentially just NONE as "do not search".
            stripped = optimized.strip().strip('".\'').upper()
            if stripped == self.NO_SEARCH_SENTINEL or stripped.startswith(self.NO_SEARCH_SENTINEL + " "):
                print("[DEBUG] Optimizer says no search needed")
                return None

            # Validate result - if empty or too long, use original
            if not optimized or len(optimized) > 100 or len(optimized) < 3:
                print(f"[DEBUG] Query optimization failed, using original")
                return user_message
            
            print(f"[DEBUG] Optimized query: '{user_message}' -> '{optimized}'")
            return optimized
            
        except Exception as e:
            print(f"[DEBUG] Query optimization error: {e}, using original")
            return user_message
    
    def _get_token_limit_instruction(self, max_tokens: int) -> str:
        """Generate instruction to limit response length.
        
        This helps the LLM understand token constraints and respond appropriately.
        """
        if max_tokens < 300:
            guidance = "Keep your response very brief (1-2 sentences)."
        elif max_tokens < 500:
            guidance = "Keep your response concise (2-4 sentences)."
        elif max_tokens < 1000:
            guidance = "Keep your response moderately detailed (3-5 paragraphs)."
        elif max_tokens < 2000:
            guidance = "Provide a comprehensive response with good detail."
        else:
            guidance = "Provide thorough, detailed responses as needed."
        
        return f"\nIMPORTANT: Approximate token limit for response: {max_tokens} tokens. {guidance}"
    
    def _prepare_messages(
        self, 
        user_message: str
    ) -> tuple[List[Dict[str, str]], List[Source], Optional[Dict[str, Any]]]:
        """Prepare messages for LLM based on current mode.
        
        Returns:
            Tuple of (messages, sources, search_metadata)
            search_metadata contains 'query' and 'results' when in search mode
        """
        if not self.current_conversation:
            self.new_conversation()
        
        sources = []
        search_metadata = None
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
            # Build conversation history for context (before adding current message)
            history = self.current_conversation.messages
            conversation_context = []
            
            # Convert to LLM format for context
            for msg in history:
                conversation_context.append(msg.to_llm_format())
            
            # Optimize the search query using LLM with full conversation context.
            # None means the message is not a search at all (a greeting, small talk),
            # in which case we skip the web entirely and answer as a normal chat -
            # system_prompt stays as the conversation's own prompt.
            optimized_query = self._optimize_search_query(user_message, conversation_context)
            if optimized_query is None:
                print(f"[DEBUG] Search skipped for: '{user_message}' - answering directly")
                search_metadata = {"query": None, "results": [], "skipped": True}
                return self._build_messages(system_prompt, user_message), sources, search_metadata

            print(f"[DEBUG] Search mode active, original: '{user_message}' -> optimized: '{optimized_query}'")

            context, search_sources = self.search_service.get_context_for_query(optimized_query)
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
                # Include search metadata for UI display
                search_metadata = {
                    "query": optimized_query,
                    "results": [
                        {"title": s["title"], "url": s.get("url", ""), "snippet": s["content"][:150]}
                        for s in search_sources
                    ]
                }
            else:
                print("[DEBUG] No search context returned!")
        
        return self._build_messages(system_prompt, user_message), sources, search_metadata

    def _build_messages(self, system_prompt: str, user_message: str) -> List[Dict[str, str]]:
        """Assemble the system prompt, recent history and the new user message."""
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
        return messages
    
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
    
    def summarize_context(self, keep_recent_messages: int = 4) -> Optional[str]:
        """Summarize old messages in the context file.
        
        Keeps the most recent messages intact and summarizes older ones.
        
        Args:
            keep_recent_messages: Number of recent messages to keep intact
            
        Returns:
            Summary text if successful, None otherwise
        """
        if not self.current_conversation or not self.llm_service or not self.llm_service.is_loaded:
            return None
        
        try:
            messages = self.current_conversation.messages
            if len(messages) == 0:
                return None  # No messages to summarize
            
            # If fewer messages than keep_recent, summarize all and keep none separate
            if len(messages) <= keep_recent_messages:
                messages_to_summarize = messages
                keep_recent_messages = 0
            else:
                # Messages to summarize (all except recent ones)
                messages_to_summarize = messages[:-keep_recent_messages]
            
            # Build text to summarize
            summary_text = f"System Prompt: {self.current_conversation.system_prompt}\n\n"
            for msg in messages_to_summarize:
                role = "User" if msg.role == MessageRole.USER else "Assistant"
                summary_text += f"{role}: {msg.content}\n\n"
            
            # Create summarization prompt
            summarize_prompt = f"""Please create a concise summary of this conversation excerpt. 
Focus on key information, decisions, and context that would be useful for continuing the conversation.
Keep the summary under 200 words.

Conversation to summarize:
{summary_text}

Summary:"""
            
            # Generate summary
            result = self.llm_service.generate(
                messages=[{"role": "user", "content": summarize_prompt}],
                max_tokens=256,
                temperature=0.3,
            )
            
            summary = result.strip()
            
            # Update context file with summary
            context_file = Path(self.conversations_dir) / f"{self.current_conversation.id}.context.md"
            
            context_lines = []
            
            # System prompt
            if self.current_conversation.system_prompt:
                context_lines.append("# System Prompt")
                context_lines.append(self.current_conversation.system_prompt)
                context_lines.append("")
                context_lines.append("---")
                context_lines.append("")
            
            # Add summary
            context_lines.append("## Summary of Earlier Discussion")
            context_lines.append(summary)
            context_lines.append("")
            context_lines.append("---")
            context_lines.append("")
            
            # Add recent messages (if any kept separate from summary)
            if keep_recent_messages > 0:
                for msg in self.current_conversation.messages[-keep_recent_messages:]:
                    role_header = "## User" if msg.role == MessageRole.USER else "## Assistant"
                    context_lines.append(role_header)
                    context_lines.append(msg.content)
                    context_lines.append("")
            
            # Write updated context
            with open(context_file, "w", encoding="utf-8") as f:
                f.write("\n".join(context_lines))
            
            print(f"[DEBUG] Context summarized successfully. Summary: {len(summary)} chars")
            return summary
            
        except Exception as e:
            print(f"[DEBUG] Context summarization error: {e}")
            return None
    
    def get_mode(self) -> ChatMode:
        """Get the current chat mode."""
        return self.mode
