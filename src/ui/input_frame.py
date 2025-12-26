"""Message input frame with text entry and send button."""

import customtkinter as ctk
from typing import Callable, Optional


class InputFrame(ctk.CTkFrame):
    """Frame containing message input and send button."""
    
    def __init__(
        self, 
        parent, 
        on_send: Callable[[str], None],
        on_stop: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.on_send = on_send
        self.on_stop = on_stop
        self._is_generating = False
        
        self.configure(fg_color="transparent")
        
        # Main container
        self.container = ctk.CTkFrame(self, fg_color="#2D2D2D", corner_radius=20)
        self.container.pack(fill="x", padx=20, pady=10)
        
        # Text input
        self.text_input = ctk.CTkTextbox(
            self.container,
            height=60,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            border_width=0,
            wrap="word",
        )
        self.text_input.pack(side="left", fill="both", expand=True, padx=(15, 5), pady=10)
        
        # Bind Enter key (Shift+Enter for newline)
        self.text_input.bind("<Return>", self._on_enter)
        self.text_input.bind("<Shift-Return>", self._on_shift_enter)
        
        # Send button
        self.send_button = ctk.CTkButton(
            self.container,
            text="Send",
            width=70,
            height=40,
            font=ctk.CTkFont(size=14),
            command=self._send_message,
        )
        self.send_button.pack(side="right", padx=(5, 15), pady=10)
    
    def _on_enter(self, event):
        """Handle Enter key press."""
        if not event.state & 0x1:  # Shift not pressed
            self._send_message()
            return "break"  # Prevent newline
        return None
    
    def _on_shift_enter(self, event):
        """Handle Shift+Enter for newline."""
        return None  # Allow default behavior
    
    def _send_message(self):
        """Send the message."""
        if self._is_generating:
            if self.on_stop:
                self.on_stop()
            return
        
        message = self.text_input.get("1.0", "end-1c").strip()
        if message:
            self.text_input.delete("1.0", "end")
            self.on_send(message)
    
    def set_generating(self, is_generating: bool):
        """Set the generating state."""
        self._is_generating = is_generating
        if is_generating:
            self.send_button.configure(text="Stop", fg_color="#AA4444")
            self.text_input.configure(state="disabled")
        else:
            self.send_button.configure(text="Send", fg_color=["#3B8ED0", "#1F6AA5"])
            self.text_input.configure(state="normal")
            self.text_input.focus_set()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable input."""
        if enabled:
            self.text_input.configure(state="normal")
            self.send_button.configure(state="normal")
        else:
            self.text_input.configure(state="disabled")
            self.send_button.configure(state="disabled")
    
    def focus_input(self):
        """Focus the text input."""
        self.text_input.focus_set()
