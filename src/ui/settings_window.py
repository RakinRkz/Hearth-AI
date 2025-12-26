"""Settings window for application configuration."""

import customtkinter as ctk
from typing import Callable, Optional
from pathlib import Path
from tkinter import filedialog


class SettingsWindow(ctk.CTkToplevel):
    """Settings dialog window."""
    
    def __init__(
        self,
        parent,
        current_config: dict,
        on_save: Callable[[dict], None],
        on_load_model: Callable[[str], None],
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.current_config = current_config
        self.on_save = on_save
        self.on_load_model = on_load_model
        
        self.title("Settings")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        
        self._setup_ui()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Grab focus after window is visible
        self.after(100, self._grab_focus)
    
    def _grab_focus(self):
        """Grab focus after window is visible."""
        try:
            self.grab_set()
            self.focus_set()
        except Exception:
            pass  # Ignore if grab fails
    
    def _setup_ui(self):
        """Set up the settings UI."""
        # Scrollable container
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Model Settings
        self._add_section(container, "Model Settings")
        
        # Model path
        model_frame = ctk.CTkFrame(container, fg_color="transparent")
        model_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(model_frame, text="Model Path:", font=ctk.CTkFont(size=13)).pack(anchor="w")
        
        model_input_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        model_input_frame.pack(fill="x", pady=5)
        
        self.model_path_var = ctk.StringVar(value=self.current_config.get("model_path", ""))
        self.model_entry = ctk.CTkEntry(
            model_input_frame,
            textvariable=self.model_path_var,
            width=300,
        )
        self.model_entry.pack(side="left", fill="x", expand=True)
        
        browse_btn = ctk.CTkButton(
            model_input_frame,
            text="Browse",
            width=70,
            command=self._browse_model,
        )
        browse_btn.pack(side="left", padx=(10, 0))
        
        load_btn = ctk.CTkButton(
            model_input_frame,
            text="Load",
            width=60,
            fg_color="green",
            command=self._load_model,
        )
        load_btn.pack(side="left", padx=(10, 0))
        
        # Download model button
        download_frame = ctk.CTkFrame(container, fg_color="transparent")
        download_frame.pack(fill="x", pady=(5, 0))
        
        download_btn = ctk.CTkButton(
            download_frame,
            text="📥 Download Recommended Model",
            fg_color="#1a5f7a",
            command=self._open_download_wizard,
        )
        download_btn.pack(side="left")
        
        # Context length
        self._add_slider(
            container, "Context Length", "context_length",
            512, 8192, self.current_config.get("context_length", 4096)
        )
        
        # GPU layers
        self._add_slider(
            container, "GPU Layers (-1=All GPU, 0=CPU only)", "gpu_layers",
            -1, 100, self.current_config.get("gpu_layers", -1)
        )
        
        # Generation Settings
        self._add_section(container, "Generation Settings")
        
        # Temperature
        self._add_slider(
            container, "Temperature", "temperature",
            0.0, 2.0, self.current_config.get("temperature", 0.7),
            resolution=0.1
        )
        
        # Top P
        self._add_slider(
            container, "Top P", "top_p",
            0.0, 1.0, self.current_config.get("top_p", 0.9),
            resolution=0.05
        )
        
        # Max tokens
        self._add_slider(
            container, "Max Tokens", "max_tokens",
            64, 4096, self.current_config.get("max_tokens", 1024)
        )
        
        # RAG Settings
        self._add_section(container, "RAG Settings")
        
        # Chunk size
        self._add_slider(
            container, "Chunk Size", "chunk_size",
            100, 2000, self.current_config.get("chunk_size", 500)
        )
        
        # Top K results
        self._add_slider(
            container, "Top K Results", "top_k_results",
            1, 10, self.current_config.get("top_k_results", 4)
        )
        
        # Search Settings
        self._add_section(container, "Web Search Settings")
        
        # Max search results
        self._add_slider(
            container, "Max Search Results", "max_search_results",
            1, 10, self.current_config.get("max_search_results", 5)
        )
        
        # UI Settings
        self._add_section(container, "UI Settings")
        
        # Theme
        theme_frame = ctk.CTkFrame(container, fg_color="transparent")
        theme_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(theme_frame, text="Theme:", font=ctk.CTkFont(size=13)).pack(side="left")
        
        self.theme_var = ctk.StringVar(value=self.current_config.get("theme", "dark"))
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            variable=self.theme_var,
            values=["dark", "light", "system"],
            command=self._change_theme,
        )
        theme_menu.pack(side="right")
        
        # Save button
        save_frame = ctk.CTkFrame(self, fg_color="transparent")
        save_frame.pack(fill="x", padx=20, pady=20)
        
        save_btn = ctk.CTkButton(
            save_frame,
            text="Save Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._save_settings,
        )
        save_btn.pack(fill="x")
    
    def _add_section(self, parent, title: str):
        """Add a section header."""
        label = ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        label.pack(anchor="w", pady=(20, 10))
        
        sep = ctk.CTkFrame(parent, fg_color="#333333", height=1)
        sep.pack(fill="x", pady=(0, 10))
    
    def _add_slider(
        self, 
        parent, 
        label: str, 
        key: str, 
        from_: float, 
        to: float, 
        default: float,
        resolution: float = 1
    ):
        """Add a labeled slider."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        # Label and value
        label_frame = ctk.CTkFrame(frame, fg_color="transparent")
        label_frame.pack(fill="x")
        
        ctk.CTkLabel(label_frame, text=label, font=ctk.CTkFont(size=13)).pack(side="left")
        
        value_label = ctk.CTkLabel(
            label_frame,
            text=str(default),
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        value_label.pack(side="right")
        
        # Slider
        def update_value(val):
            if resolution >= 1:
                val = int(float(val))
            else:
                val = round(float(val), 2)
            value_label.configure(text=str(val))
            setattr(self, f"_{key}_value", val)
        
        slider = ctk.CTkSlider(
            frame,
            from_=from_,
            to=to,
            number_of_steps=int((to - from_) / resolution) if resolution else 100,
            command=update_value,
        )
        slider.set(default)
        slider.pack(fill="x", pady=(5, 0))
        
        setattr(self, f"_{key}_value", default)
    
    def _browse_model(self):
        """Browse for model file."""
        file_path = filedialog.askopenfilename(
            title="Select GGUF Model",
            filetypes=[("GGUF models", "*.gguf"), ("All files", "*.*")],
            initialdir=self.current_config.get("models_dir", "models"),
        )
        if file_path:
            self.model_path_var.set(file_path)
    
    def _load_model(self):
        """Load the selected model."""
        model_path = self.model_path_var.get()
        if model_path:
            self.on_load_model(model_path)
    
    def _change_theme(self, theme: str):
        """Change the application theme."""
        ctk.set_appearance_mode(theme)
    
    def _open_download_wizard(self):
        """Open the setup wizard to download a model."""
        from .setup_wizard import SetupWizard
        
        def on_download_complete(model_path: str):
            self.model_path_var.set(model_path)
            self.on_load_model(model_path)
        
        wizard = SetupWizard(
            self,
            on_complete=on_download_complete,
            on_skip=None,
        )
    
    def _save_settings(self):
        """Save settings and close."""
        config = {
            "model_path": self.model_path_var.get(),
            "context_length": int(getattr(self, "_context_length_value", 4096)),
            "gpu_layers": int(getattr(self, "_gpu_layers_value", -1)),
            "temperature": getattr(self, "_temperature_value", 0.7),
            "top_p": getattr(self, "_top_p_value", 0.9),
            "max_tokens": int(getattr(self, "_max_tokens_value", 1024)),
            "chunk_size": int(getattr(self, "_chunk_size_value", 500)),
            "top_k_results": int(getattr(self, "_top_k_results_value", 4)),
            "max_search_results": int(getattr(self, "_max_search_results_value", 5)),
            "theme": self.theme_var.get(),
        }
        
        self.on_save(config)
        self.destroy()
