"""Main application window."""

import customtkinter as ctk
from typing import Optional
from pathlib import Path

from .chat_frame import ChatFrame
from .input_frame import InputFrame
from .sidebar import Sidebar
from .settings_window import SettingsWindow
from .setup_wizard import SetupWizard

# Use absolute imports for sibling packages
import sys
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from services import LLMService, EmbeddingService, RAGService, SearchService, ChatService
from services.chat_service import ChatMode
from models import MessageRole
from utils.config import get_config, get_config_manager


class MainWindow(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Hearth AI")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Set theme
        config = get_config()
        ctk.set_appearance_mode(config.theme)
        ctk.set_default_color_theme("blue")
        
        # Initialize services
        self._init_services()
        
        # Setup UI
        self._setup_ui()
        
        # Load initial state
        self._load_initial_state()
    
    def _init_services(self):
        """Initialize application services."""
        config = get_config()
        
        # LLM service
        self.llm_service = LLMService(
            context_length=config.context_length,
            gpu_layers=config.gpu_layers,
        )
        
        # Embedding service (lazy loaded)
        self.embedding_service = None
        
        # RAG service (lazy loaded - requires chromadb)
        self.rag_service = None
        
        # Search service (lazy loaded - requires duckduckgo-search)
        self.search_service = None
        
        # Chat service
        app_dir = Path(__file__).parent.parent.parent
        self.chat_service = ChatService(
            llm_service=self.llm_service,
            rag_service=None,  # Will be set when needed
            search_service=None,  # Will be set when needed
            conversations_dir=str(app_dir / config.data_dir / "conversations"),
        )
        
        # State
        self._is_generating = False
        self._streaming_text = ""
    
    def _init_rag_service(self):
        """Initialize RAG service on demand."""
        if self.rag_service is not None:
            return True
        
        try:
            config = get_config()
            
            # Initialize embedding service
            if self.embedding_service is None:
                self.embedding_service = EmbeddingService(
                    model_name=config.embedding_model
                )
            
            # Initialize RAG service
            app_dir = Path(__file__).parent.parent.parent
            self.rag_service = RAGService(
                embedding_service=self.embedding_service,
                persist_directory=str(app_dir / config.data_dir / "vectorstore"),
            )
            
            # Update chat service
            self.chat_service.rag_service = self.rag_service
            return True
            
        except ImportError as e:
            self._show_error(f"RAG requires additional packages:\npip install chromadb sentence-transformers")
            return False
    
    def _init_search_service(self):
        """Initialize search service on demand."""
        if self.search_service is not None:
            return True
        
        try:
            config = get_config()
            self.search_service = SearchService(
                max_results=config.max_search_results
            )
            
            # Update chat service
            self.chat_service.search_service = self.search_service
            return True
            
        except ImportError as e:
            self._show_error(f"Web search requires additional packages:\npip install duckduckgo-search")
            return False
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = Sidebar(
            self,
            on_mode_change=self._on_mode_change,
            on_new_chat=self._on_new_chat,
            on_load_chat=self._on_load_chat,
            on_delete_chat=self._on_delete_chat,
            on_upload_document=self._on_upload_document,
            on_remove_document=self._on_remove_document,
            on_settings=self._on_settings,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Main content area
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 0))
        main_frame.grid_rowconfigure(1, weight=1)  # Chat frame gets the weight
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Mode indicator banner
        self.mode_banner = ctk.CTkFrame(main_frame, fg_color="#1e3a5f", height=35, corner_radius=8)
        self.mode_banner.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.mode_banner.grid_remove()  # Hidden by default for chat mode
        
        self.mode_banner_label = ctk.CTkLabel(
            self.mode_banner,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="white",
        )
        self.mode_banner_label.pack(pady=8)
        
        # Chat frame
        self.chat_frame = ChatFrame(main_frame)
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 0))
        
        # Input frame
        self.input_frame = InputFrame(
            main_frame,
            on_send=self._on_send_message,
            on_stop=self._on_stop_generation,
        )
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
    
    def _load_initial_state(self):
        """Load initial application state."""
        # Update conversations list
        self._refresh_conversations()
        
        # Update documents list
        self._refresh_documents()
        
        # Check for first run or missing model
        config = get_config()
        config_manager = get_config_manager()
        
        # Check if we need to show setup wizard
        show_setup = False
        if config.first_run:
            show_setup = True
        elif not config.model_path or not Path(config.model_path).exists():
            # No model configured or model file missing
            show_setup = True
        
        if show_setup:
            # Show setup wizard
            self.after(500, self._show_setup_wizard)
        else:
            # Try to load configured model
            self._load_model(config.model_path)
        
        # Create new conversation
        self._on_new_chat()
        
        # Focus input
        self.input_frame.focus_input()
    
    def _show_setup_wizard(self):
        """Show the first-run setup wizard."""
        wizard = SetupWizard(
            self,
            on_complete=self._on_setup_complete,
            on_skip=self._on_setup_skip,
        )
    
    def _on_setup_complete(self, model_path: str):
        """Handle setup wizard completion."""
        config_manager = get_config_manager()
        config_manager.update(first_run=False, model_path=model_path)
        
        # Load the model
        self._load_model(model_path)
    
    def _on_setup_skip(self):
        """Handle setup wizard skip."""
        config_manager = get_config_manager()
        config_manager.update(first_run=False)
        
        # Show hint in chat
        self.chat_frame.add_message(
            "Welcome to Hearth AI!\n\n"
            "To start chatting, you'll need to load an AI model:\n\n"
            "1. Click the Settings button in the sidebar\n"
            "2. Select a model file (.gguf format)\n"
            "3. Start chatting!\n\n"
            "You can download models from Hugging Face or use the setup wizard from Settings.",
            is_user=False,
        )
    
    def _load_model(self, model_path: str):
        """Load an LLM model."""
        try:
            self.sidebar.set_model_status(False, "Loading...")
            self.update()
            
            self.llm_service.load_model(model_path)
            self.sidebar.set_model_status(True, model_path)
            
            # Save to config
            config_manager = get_config_manager()
            config_manager.update(model_path=model_path)
            
        except Exception as e:
            self.sidebar.set_model_status(False)
            self._show_error(f"Failed to load model: {e}")
    
    def _on_mode_change(self, mode: str):
        """Handle mode change."""
        # Initialize services on demand
        if mode == "rag":
            if not self._init_rag_service():
                self.sidebar.set_mode("chat")
                return
            # Show RAG mode banner
            self.mode_banner_label.configure(text="RAG Mode - Questions will use your uploaded documents as context")
            self.mode_banner.configure(fg_color="#2d5a27")  # Green
            self.mode_banner.grid()
        elif mode == "search":
            if not self._init_search_service():
                self.sidebar.set_mode("chat")
                return
            # Show search mode banner
            self.mode_banner_label.configure(text="Web Search Mode - Questions will search the web for real-time info")
            self.mode_banner.configure(fg_color="#1e3a5f")  # Blue
            self.mode_banner.grid()
        else:
            # Hide banner for chat mode
            self.mode_banner.grid_remove()
        
        mode_map = {
            "chat": ChatMode.CHAT,
            "rag": ChatMode.RAG,
            "search": ChatMode.SEARCH,
        }
        self.chat_service.set_mode(mode_map.get(mode, ChatMode.CHAT))
    
    def _on_new_chat(self):
        """Create a new chat conversation."""
        self.chat_service.new_conversation()
        self.chat_frame.clear()
        self._refresh_conversations()
        self.input_frame.focus_input()
    
    def _on_load_chat(self, conversation_id: str):
        """Load an existing conversation."""
        conv = self.chat_service.load_conversation(conversation_id)
        if conv:
            self.chat_frame.clear()
            # Replay messages
            for msg in conv.messages:
                self.chat_frame.add_message(
                    msg.content,
                    is_user=(msg.role == MessageRole.USER),
                    sources=msg.sources,
                    timestamp=msg.timestamp,
                )
    
    def _on_delete_chat(self, conversation_id: str):
        """Delete a conversation."""
        self.chat_service.delete_conversation(conversation_id)
        self._refresh_conversations()
        
        # If deleted current, create new
        if (self.chat_service.current_conversation and 
            self.chat_service.current_conversation.id == conversation_id):
            self._on_new_chat()
    
    def _on_upload_document(self, file_path: str):
        """Upload and index a document."""
        # Initialize RAG service if needed
        if not self._init_rag_service():
            return
        
        try:
            self.sidebar.set_model_status(False, "Indexing...")
            self.update()
            
            num_chunks = self.rag_service.add_document(file_path)
            self._refresh_documents()
            
            # Restore model status
            config = get_config()
            self.sidebar.set_model_status(
                self.llm_service.is_loaded, 
                config.model_path or ""
            )
            
            self._show_info(f"Indexed {num_chunks} chunks from {Path(file_path).name}")
            
        except Exception as e:
            self._show_error(f"Failed to index document: {e}")
            config = get_config()
            self.sidebar.set_model_status(
                self.llm_service.is_loaded,
                config.model_path or ""
            )
    
    def _on_remove_document(self, file_path: str):
        """Remove a document from the index."""
        if self.rag_service:
            self.rag_service.remove_document(file_path)
            self._refresh_documents()
    
    def _on_settings(self):
        """Open settings window."""
        config = get_config()
        SettingsWindow(
            self,
            current_config={
                "model_path": config.model_path or "",
                "context_length": config.context_length,
                "gpu_layers": config.gpu_layers,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "max_tokens": config.max_tokens,
                "chunk_size": config.chunk_size,
                "top_k_results": config.top_k_results,
                "max_search_results": config.max_search_results,
                "theme": config.theme,
            },
            on_save=self._on_save_settings,
            on_load_model=self._load_model,
        )
    
    def _on_save_settings(self, new_config: dict):
        """Save settings."""
        config_manager = get_config_manager()
        config_manager.update(**new_config)
        
        # Update services with new config (only if initialized)
        config = get_config()
        if self.search_service is not None:
            self.search_service.max_results = config.max_search_results
        if self.rag_service is not None and hasattr(self.rag_service, '_document_loader'):
            self.rag_service._document_loader.chunk_size = config.chunk_size
    
    def _on_send_message(self, message: str):
        """Send a message."""
        if not message.strip():
            return
        
        if not self.llm_service.is_loaded:
            self._show_error("Please load a model first (Settings → Browse → Load)")
            return
        
        # If already generating, stop the current generation first
        if self._is_generating:
            print("[DEBUG] New message while generating - stopping previous generation")
            self._on_stop_generation()
            # Small delay to let cancellation take effect
            self.after(100, lambda: self._send_message_internal(message))
            return
        
        self._send_message_internal(message)
    
    def _send_message_internal(self, message: str):
        """Internal method to send message after checks."""
        # Add user message to UI
        self.chat_frame.add_message(message, is_user=True)
        
        # Start streaming response
        self._is_generating = True
        self._streaming_text = ""
        self.input_frame.set_generating(True)
        
        # Start assistant bubble
        self.chat_frame.start_streaming()
        
        config = get_config()
        
        # Send message with streaming
        self.chat_service.send_message_async(
            user_message=message,
            on_token=self._on_token_received,
            on_complete=self._on_generation_complete,
            on_error=self._on_generation_error,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )
    
    def _on_token_received(self, token: str):
        """Handle received token during streaming."""
        self._streaming_text += token
        self.chat_frame.update_streaming(self._streaming_text)
    
    def _on_generation_complete(self, message):
        """Handle generation completion."""
        self._is_generating = False
        self.input_frame.set_generating(False)
        self.chat_frame.finish_streaming(
            self._streaming_text, 
            sources=message.sources if message else None
        )
        self._refresh_conversations()
    
    def _on_generation_error(self, error: Exception):
        """Handle generation error."""
        self._is_generating = False
        self.input_frame.set_generating(False)
        self.chat_frame.finish_streaming(f"Error: {error}")
        self._show_error(str(error))
    
    def _on_stop_generation(self):
        """Stop the current generation."""
        print("[DEBUG] Stop button pressed, cancelling generation...")
        
        # Cancel in LLM service
        if self.llm_service:
            self.llm_service.cancel_generation()
        
        # Update UI state
        self._is_generating = False
        self.input_frame.set_generating(False)
        
        # Mark the current message as stopped
        self.chat_frame.finish_streaming(" [Stopped]")
    
    def _refresh_conversations(self):
        """Refresh the conversations list."""
        conversations = self.chat_service.list_conversations()
        self.sidebar.update_conversations(conversations)
    
    def _refresh_documents(self):
        """Refresh the documents list."""
        if self.rag_service:
            documents = self.rag_service.get_indexed_documents()
        else:
            documents = []
        self.sidebar.update_documents(documents)
    
    def _show_error(self, message: str):
        """Show an error message."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(
            dialog,
            text="❌ Error",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            dialog,
            text=message,
            wraplength=350,
        ).pack(pady=5)
        
        ctk.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy,
        ).pack(pady=15)
    
    def _show_info(self, message: str):
        """Show an info message."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Info")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(
            dialog,
            text="ℹ️ Info",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            dialog,
            text=message,
            wraplength=350,
        ).pack(pady=5)
        
        ctk.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy,
        ).pack(pady=15)
