"""Sidebar with mode selection, conversations, and documents."""

import customtkinter as ctk
from typing import Callable, Optional, List, Dict, Any
from pathlib import Path
from tkinter import filedialog


class Sidebar(ctk.CTkFrame):
    """Sidebar with mode selection, conversations, and document management."""
    
    def __init__(
        self,
        parent,
        on_mode_change: Callable[[str], None],
        on_new_chat: Callable[[], None],
        on_load_chat: Callable[[str], None],
        on_delete_chat: Callable[[str], None],
        on_upload_document: Callable[[str], None],
        on_remove_document: Callable[[str], None],
        on_settings: Callable[[], None],
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.on_mode_change = on_mode_change
        self.on_new_chat = on_new_chat
        self.on_load_chat = on_load_chat
        self.on_delete_chat = on_delete_chat
        self.on_upload_document = on_upload_document
        self.on_remove_document = on_remove_document
        self.on_settings = on_settings
        
        self.configure(fg_color="#1A1A1A", width=280)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the sidebar UI."""
        # App title
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        title = ctk.CTkLabel(
            title_frame,
            text="AI Chat",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(side="left")
        
        # Settings button
        settings_btn = ctk.CTkButton(
            title_frame,
            text="Settings",
            width=60,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#333333",
            hover_color="#444444",
            command=self.on_settings,
        )
        settings_btn.pack(side="right")
        
        # New chat button
        self.new_chat_btn = ctk.CTkButton(
            self,
            text="+ New Chat",
            font=ctk.CTkFont(size=14),
            height=40,
            command=self.on_new_chat,
        )
        self.new_chat_btn.pack(fill="x", padx=15, pady=(5, 15))
        
        # Mode selection
        mode_label = ctk.CTkLabel(
            self,
            text="Mode",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
        )
        mode_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.mode_var = ctk.StringVar(value="chat")
        
        # Mode selection frame with better visibility
        mode_frame = ctk.CTkFrame(self, fg_color="#252525", corner_radius=8)
        mode_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        modes = [
            ("Chat", "chat", "Regular conversation"),
            ("RAG (Documents)", "rag", "Query your documents"),
            ("Web Search", "search", "Search the internet"),
        ]
        
        for label, value, tooltip in modes:
            rb = ctk.CTkRadioButton(
                mode_frame,
                text=label,
                variable=self.mode_var,
                value=value,
                font=ctk.CTkFont(size=13),
                command=lambda v=value: self.on_mode_change(v),
                radiobutton_width=18,
                radiobutton_height=18,
            )
            rb.pack(anchor="w", padx=15, pady=6)
        
        # Separator
        sep = ctk.CTkFrame(self, fg_color="#333333", height=1)
        sep.pack(fill="x", padx=15, pady=15)
        
        # Conversations section
        conv_header = ctk.CTkFrame(self, fg_color="transparent")
        conv_header.pack(fill="x", padx=15)
        
        conv_label = ctk.CTkLabel(
            conv_header,
            text="Conversations",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
        )
        conv_label.pack(side="left")
        
        # Conversations list
        self.conv_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=150,
        )
        self.conv_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        # Separator
        sep2 = ctk.CTkFrame(self, fg_color="#333333", height=1)
        sep2.pack(fill="x", padx=15, pady=10)
        
        # Documents section
        docs_header = ctk.CTkFrame(self, fg_color="transparent")
        docs_header.pack(fill="x", padx=15)
        
        docs_label = ctk.CTkLabel(
            docs_header,
            text="Documents",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
        )
        docs_label.pack(side="left")
        
        upload_btn = ctk.CTkButton(
            docs_header,
            text="+ Upload",
            width=70,
            height=25,
            font=ctk.CTkFont(size=11),
            command=self._upload_document,
        )
        upload_btn.pack(side="right")
        
        # Documents list
        self.docs_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=120,
        )
        self.docs_frame.pack(fill="both", expand=True, padx=5, pady=(5, 15))
        
        # Model status at bottom
        self.status_frame = ctk.CTkFrame(self, fg_color="#222222", corner_radius=10)
        self.status_frame.pack(fill="x", padx=15, pady=(0, 15), side="bottom")
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="[!] No model loaded",
            font=ctk.CTkFont(size=11),
            text_color="orange",
        )
        self.status_label.pack(padx=10, pady=8)
    
    def _upload_document(self):
        """Open file dialog to upload a document."""
        filetypes = [
            ("All supported", "*.pdf *.txt *.md *.docx"),
            ("PDF files", "*.pdf"),
            ("Text files", "*.txt"),
            ("Markdown files", "*.md"),
            ("Word documents", "*.docx"),
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Document",
            filetypes=filetypes,
        )
        
        if file_path:
            self.on_upload_document(file_path)
    
    def update_conversations(self, conversations: List[Dict[str, Any]]):
        """Update the conversations list."""
        # Clear existing - use after_idle to avoid tkinter callback issues
        def _clear_and_update():
            for widget in list(self.conv_frame.winfo_children()):
                try:
                    widget.destroy()
                except Exception:
                    pass
            
            if not conversations:
                empty_label = ctk.CTkLabel(
                    self.conv_frame,
                    text="No conversations yet",
                    font=ctk.CTkFont(size=12),
                    text_color="gray",
                )
                empty_label.pack(pady=10)
                return
            
            for conv in conversations[:10]:  # Show max 10
                self._add_conversation_item(conv)
        
        self.after_idle(_clear_and_update)
    
    def _add_conversation_item(self, conv: Dict[str, Any]):
        """Add a conversation item to the list."""
        frame = ctk.CTkFrame(self.conv_frame, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        
        btn = ctk.CTkButton(
            frame,
            text=conv["title"][:25] + "..." if len(conv["title"]) > 25 else conv["title"],
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#333333",
            anchor="w",
            height=30,
            command=lambda c=conv["id"]: self.on_load_chat(c),
        )
        btn.pack(side="left", fill="x", expand=True)
        
        del_btn = ctk.CTkButton(
            frame,
            text="x",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#AA4444",
            font=ctk.CTkFont(size=12),
            command=lambda c=conv["id"]: self.on_delete_chat(c),
        )
        del_btn.pack(side="right")
    
    def update_documents(self, documents: List[Dict[str, Any]]):
        """Update the documents list."""
        # Clear existing - use after_idle to avoid tkinter callback issues
        def _clear_and_update():
            for widget in list(self.docs_frame.winfo_children()):
                try:
                    widget.destroy()
                except Exception:
                    pass
            
            if not documents:
                empty_label = ctk.CTkLabel(
                    self.docs_frame,
                    text="No documents uploaded",
                    font=ctk.CTkFont(size=12),
                    text_color="gray",
                )
                empty_label.pack(pady=10)
                return
            
            for doc in documents:
                self._add_document_item(doc)
        
        self.after_idle(_clear_and_update)
    
    def _add_document_item(self, doc: Dict[str, Any]):
        """Add a document item to the list."""
        frame = ctk.CTkFrame(self.docs_frame, fg_color="#2D2D2D", corner_radius=8)
        frame.pack(fill="x", pady=2, padx=5)
        
        # Icon based on extension
        ext = Path(doc["name"]).suffix.lower()
        icon = {"pdf": "[PDF]", "txt": "[TXT]", "md": "[MD]", "docx": "[DOC]"}.get(ext, "[FILE]")
        
        label = ctk.CTkLabel(
            frame,
            text=f"{icon} {doc['name'][:18]}{'...' if len(doc['name']) > 18 else ''}",
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        label.pack(side="left", padx=10, pady=5)
        
        del_btn = ctk.CTkButton(
            frame,
            text="✕",
            width=25,
            height=25,
            fg_color="transparent",
            hover_color="#AA4444",
            font=ctk.CTkFont(size=10),
            command=lambda p=doc["path"]: self.on_remove_document(p),
        )
        del_btn.pack(side="right", padx=5)
    
    def set_mode(self, mode: str):
        """Set the current mode."""
        self.mode_var.set(mode)
    
    def set_model_status(self, loaded: bool, model_name: str = ""):
        """Update the model status display."""
        if loaded:
            name = Path(model_name).stem if model_name else "Model"
            name = name[:20] + "..." if len(name) > 20 else name
            self.status_label.configure(
                text=f"[OK] {name}",
                text_color="#4CAF50",
            )
        else:
            self.status_label.configure(
                text="[!] No model loaded",
                text_color="orange",
            )
