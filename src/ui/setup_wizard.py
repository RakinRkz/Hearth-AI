"""First-run setup wizard for downloading models."""

import customtkinter as ctk
from typing import Optional, Callable
from pathlib import Path


class SetupWizard(ctk.CTkToplevel):
    """First-run setup wizard for downloading a default model."""
    
    def __init__(
        self,
        parent,
        on_complete: Optional[Callable[[str], None]] = None,
        on_skip: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        
        self.on_complete = on_complete
        self.on_skip = on_skip
        self._downloader = None
        self._is_downloading = False
        
        # Window setup
        self.title("Welcome to AI Chat")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        
        # Make modal after a short delay
        self.after(100, self._make_modal)
        
        # Setup UI
        self._setup_ui()
        
        # Load model info
        self._load_model_info()
        
        # Handle close button
        self.protocol("WM_DELETE_WINDOW", self._on_skip)
    
    def _make_modal(self):
        """Make window modal."""
        try:
            self.grab_set()
        except:
            pass
    
    def _setup_ui(self):
        """Setup the wizard UI."""
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Welcome header
        header = ctk.CTkLabel(
            container,
            text="Welcome to AI Chat! 🤖",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        header.pack(pady=(0, 10))
        
        # Subtitle
        subtitle = ctk.CTkLabel(
            container,
            text="Let's set up your local AI model",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        subtitle.pack(pady=(0, 20))
        
        # Info box
        info_frame = ctk.CTkFrame(container)
        info_frame.pack(fill="x", pady=(0, 20))
        
        info_text = ctk.CTkLabel(
            info_frame,
            text="AI Chat runs entirely on your computer - no internet required!\n"
                 "To get started, we'll download a pre-trained language model.\n\n"
                 "This only needs to be done once.",
            font=ctk.CTkFont(size=13),
            justify="left",
            wraplength=500,
        )
        info_text.pack(padx=20, pady=15)
        
        # Model selection frame
        model_frame = ctk.CTkFrame(container)
        model_frame.pack(fill="x", pady=(0, 20))
        
        model_header = ctk.CTkLabel(
            model_frame,
            text="Recommended Model",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        model_header.pack(anchor="w", padx=20, pady=(15, 5))
        
        # Model name
        self.model_name_label = ctk.CTkLabel(
            model_frame,
            text="Loading...",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.model_name_label.pack(anchor="w", padx=20)
        
        # Model description
        self.model_desc_label = ctk.CTkLabel(
            model_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=500,
            justify="left",
        )
        self.model_desc_label.pack(anchor="w", padx=20, pady=(5, 5))
        
        # Model size
        self.model_size_label = ctk.CTkLabel(
            model_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.model_size_label.pack(anchor="w", padx=20, pady=(0, 15))
        
        # Progress frame (hidden initially)
        self.progress_frame = ctk.CTkFrame(container)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Downloading model...",
            font=ctk.CTkFont(size=13),
        )
        self.progress_label.pack(pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)
        
        self.progress_detail = ctk.CTkLabel(
            self.progress_frame,
            text="0 MB / 0 MB",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self.progress_detail.pack(pady=(0, 10))
        
        # Buttons frame
        self.button_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.button_frame.pack(fill="x", pady=(10, 0))
        
        # Skip button
        self.skip_button = ctk.CTkButton(
            self.button_frame,
            text="Skip for Now",
            width=120,
            fg_color="transparent",
            border_width=1,
            text_color=("gray30", "gray70"),
            command=self._on_skip,
        )
        self.skip_button.pack(side="left")
        
        # Download button
        self.download_button = ctk.CTkButton(
            self.button_frame,
            text="Download & Install",
            width=180,
            command=self._on_download,
        )
        self.download_button.pack(side="right")
        
        # Cancel button (hidden initially)
        self.cancel_button = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            width=100,
            fg_color="transparent",
            border_width=1,
            text_color=("gray30", "gray70"),
            command=self._on_cancel,
        )
    
    def _load_model_info(self):
        """Load default model information."""
        try:
            from utils.model_downloader import get_model_downloader
            
            self._downloader = get_model_downloader()
            self._model = self._downloader.get_default_model()
            
            # Check if already installed
            if self._downloader.is_model_installed(self._model.filename):
                model_path = self._downloader.get_model_path(self._model.filename)
                self.model_name_label.configure(text=f"✓ {self._model.name}")
                self.model_desc_label.configure(text="This model is already installed!")
                self.model_size_label.configure(text="")
                self.download_button.configure(text="Use This Model", command=lambda: self._finish(model_path))
                return
            
            # Update UI
            self.model_name_label.configure(text=self._model.name)
            self.model_desc_label.configure(text=self._model.description)
            self.model_size_label.configure(text=f"Download size: ~{self._model.size_mb} MB")
            
        except Exception as e:
            self.model_name_label.configure(text="Error loading model info")
            self.model_desc_label.configure(text=str(e))
            self.download_button.configure(state="disabled")
    
    def _on_download(self):
        """Start model download."""
        if not self._downloader or not hasattr(self, '_model'):
            return
        
        self._is_downloading = True
        
        # Show progress UI
        self.button_frame.pack_forget()
        self.progress_frame.pack(fill="x", pady=(0, 10))
        self.button_frame.pack(fill="x", pady=(10, 0))
        
        # Update buttons
        self.skip_button.pack_forget()
        self.download_button.pack_forget()
        self.cancel_button.pack(side="right")
        
        # Start download
        self._downloader.download_model(
            self._model,
            progress_callback=self._on_progress,
            complete_callback=self._on_download_complete,
            error_callback=self._on_download_error,
        )
    
    def _on_progress(self, downloaded: int, total: int):
        """Update progress bar."""
        if total > 0:
            progress = downloaded / total
            self.progress_bar.set(progress)
            
            dl_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            percent = int(progress * 100)
            
            self.progress_detail.configure(
                text=f"{dl_mb:.1f} MB / {total_mb:.1f} MB ({percent}%)"
            )
    
    def _on_download_complete(self, model_path: str):
        """Handle download completion."""
        self._is_downloading = False
        
        # Update UI on main thread
        self.after(0, lambda: self._finish(model_path))
    
    def _on_download_error(self, error: str):
        """Handle download error."""
        self._is_downloading = False
        
        def _show_error():
            self.progress_label.configure(text=f"Download failed: {error}")
            self.progress_bar.set(0)
            
            # Restore buttons
            self.cancel_button.pack_forget()
            self.skip_button.pack(side="left")
            self.download_button.configure(text="Retry")
            self.download_button.pack(side="right")
        
        self.after(0, _show_error)
    
    def _on_cancel(self):
        """Cancel download."""
        if self._downloader:
            self._downloader.cancel_download()
        
        # Restore buttons
        self.progress_frame.pack_forget()
        self.cancel_button.pack_forget()
        self.skip_button.pack(side="left")
        self.download_button.configure(text="Download & Install")
        self.download_button.pack(side="right")
        
        self._is_downloading = False
    
    def _on_skip(self):
        """Skip setup."""
        if self._is_downloading:
            self._on_cancel()
        
        if self.on_skip:
            self.on_skip()
        
        self.destroy()
    
    def _finish(self, model_path: str):
        """Complete setup with model path."""
        if self.on_complete:
            self.on_complete(model_path)
        
        self.destroy()
