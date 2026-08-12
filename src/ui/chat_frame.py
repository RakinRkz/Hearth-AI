"""Chat message display frame."""

import customtkinter as ctk
from typing import Optional, Callable
from datetime import datetime


class MessageBubble(ctk.CTkFrame):
    """A single message bubble in the chat."""
    
    def __init__(
        self, 
        parent, 
        message: str, 
        is_user: bool = False,
        sources: list = None,
        timestamp: Optional[datetime] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.is_user = is_user
        self.sources = sources or []
        
        # Configure frame
        self.configure(
            fg_color="#2B5278" if is_user else "#2D2D2D",
            corner_radius=15,
        )
        
        # Calculate dynamic wrap length based on parent width (max 600px)
        try:
            parent_width = parent.winfo_width()
            wrap_len = min(600, max(300, int(parent_width * 0.7)))
        except:
            wrap_len = 500
        
        # Message content
        self.message_label = ctk.CTkLabel(
            self,
            text=message,
            wraplength=wrap_len,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=14),
            text_color="white",
        )
        self.message_label.pack(padx=15, pady=10, fill="x")
        
        # Sources (if any)
        if self.sources:
            self._add_sources()
        
        # Timestamp
        if timestamp:
            time_str = timestamp.strftime("%H:%M")
            self.time_label = ctk.CTkLabel(
                self,
                text=time_str,
                font=ctk.CTkFont(size=10),
                text_color="gray",
            )
            self.time_label.pack(padx=15, pady=(0, 5), anchor="e")
    
    def _add_sources(self):
        """Add source citations."""
        sources_frame = ctk.CTkFrame(self, fg_color="transparent")
        sources_frame.pack(padx=15, pady=(0, 5), fill="x")
        
        sources_label = ctk.CTkLabel(
            sources_frame,
            text="Sources:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#888888",
        )
        sources_label.pack(anchor="w")
        
        for i, source in enumerate(self.sources[:3], 1):  # Show max 3
            title = source.title if hasattr(source, 'title') else source.get('title', 'Source')
            source_text = f"[{i}] {title}"
            if hasattr(source, 'page') and source.page:
                source_text += f" (p.{source.page})"
            elif hasattr(source, 'url') and source.url:
                source_text += " 🔗"
            
            source_label = ctk.CTkLabel(
                sources_frame,
                text=source_text,
                font=ctk.CTkFont(size=10),
                text_color="#888888",
            )
            source_label.pack(anchor="w", padx=(10, 0))
    
    def update_message(self, message: str):
        """Update the message content (for streaming)."""
        self.message_label.configure(text=message)


class ChatFrame(ctk.CTkScrollableFrame):
    """Scrollable frame containing chat messages."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(fg_color="transparent")
        self.messages: list[MessageBubble] = []
        self._current_streaming_bubble: Optional[MessageBubble] = None
        
        # Welcome message
        self._show_welcome()
    
    def _show_welcome(self):
        """Show welcome message."""
        welcome_frame = ctk.CTkFrame(self, fg_color="transparent")
        welcome_frame.pack(pady=50, padx=20)
        
        title = ctk.CTkLabel(
            welcome_frame,
            text="Hearth AI",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.pack(pady=(0, 10))
        
        subtitle = ctk.CTkLabel(
            welcome_frame,
            text="Chat with a local AI • Upload documents for RAG • Search the web",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        subtitle.pack()
        
        self._welcome_frame = welcome_frame
    
    def _hide_welcome(self):
        """Hide welcome message."""
        if hasattr(self, '_welcome_frame') and self._welcome_frame:
            self._welcome_frame.destroy()
            self._welcome_frame = None
    
    def add_message(
        self, 
        message: str, 
        is_user: bool = False,
        sources: list = None,
        timestamp: Optional[datetime] = None,
    ) -> MessageBubble:
        """Add a message to the chat."""
        self._hide_welcome()
        
        # Container for alignment - fill the width
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", pady=5, padx=10)
        
        # Create bubble with max width
        bubble = MessageBubble(
            container,
            message=message,
            is_user=is_user,
            sources=sources,
            timestamp=timestamp or datetime.now(),
        )
        
        # Align right for user, left for assistant
        if is_user:
            bubble.pack(side="right", anchor="e", padx=(50, 0))  # Add left padding to push right
        else:
            bubble.pack(side="left", anchor="w", padx=(0, 50))  # Add right padding for assistant
        
        self.messages.append(bubble)
        
        # Scroll to bottom
        self.after(50, self._scroll_to_bottom)
        
        return bubble
    
    def start_streaming(self) -> MessageBubble:
        """Start a new streaming message (assistant)."""
        self._hide_welcome()
        
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", pady=5, padx=10)
        
        bubble = MessageBubble(
            container,
            message="▌",  # Cursor
            is_user=False,
        )
        bubble.pack(side="left", anchor="w", padx=(0, 50))
        
        self._current_streaming_bubble = bubble
        self.messages.append(bubble)
        
        return bubble
    
    def update_streaming(self, text: str):
        """Update the streaming message."""
        if self._current_streaming_bubble:
            self._current_streaming_bubble.update_message(text + "▌")
            self.after(10, self._scroll_to_bottom)
    
    def finish_streaming(self, text: str, sources: list = None):
        """Finish the streaming message."""
        if self._current_streaming_bubble:
            self._current_streaming_bubble.update_message(text)
            if sources:
                self._current_streaming_bubble.sources = sources
                self._current_streaming_bubble._add_sources()
            self._current_streaming_bubble = None
    
    def _scroll_to_bottom(self):
        """Scroll to the bottom of the chat."""
        self._parent_canvas.yview_moveto(1.0)
    
    def clear(self):
        """Clear all messages."""
        for widget in self.winfo_children():
            widget.destroy()
        self.messages = []
        self._current_streaming_bubble = None
        self._show_welcome()
