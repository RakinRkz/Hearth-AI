"""Model downloader utility for first-run setup."""

import os
import urllib.request
import threading
import time
from pathlib import Path
from typing import Optional, Callable, Dict, List, Tuple
from dataclasses import dataclass

from . import paths


@dataclass
class ModelInfo:
    """Information about an available model."""
    name: str
    filename: str
    url: str
    size_mb: int
    description: str
    recommended: bool = False


# Recommended starter models (small, fast, good quality)
RECOMMENDED_MODELS: List[ModelInfo] = [
    ModelInfo(
        name="Phi-3.5 Mini Instruct (3.8B)",
        filename="Phi-3.5-mini-instruct-Q4_K_M.gguf",
        url="https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf",
        size_mb=2390,
        description="Microsoft's Phi-3.5 Mini - excellent for general chat, coding, and reasoning. Recommended for most users.",
        recommended=True,
    ),
    ModelInfo(
        name="Llama 3.2 3B Instruct",
        filename="Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        url="https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        size_mb=2020,
        description="Meta's latest small model - fast and efficient for everyday tasks.",
        recommended=False,
    ),
    ModelInfo(
        name="Qwen2.5 3B Instruct",
        filename="qwen2.5-3b-instruct-q4_k_m.gguf",
        url="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
        size_mb=2050,
        description="Alibaba's Qwen 2.5 - strong multilingual and coding capabilities.",
        recommended=False,
    ),
    # TinyLlama 1.1B was offered here and had to be withdrawn: it does not
    # follow a system prompt at all. Asked "Hi" it produced an essay about
    # itself with invented articles and a fabricated support email address,
    # and with a terse prompt it decided "Hearth" was a character in a town
    # called Edenwood. No prompt wording fixed it - the failure is capability,
    # not phrasing. Llama 3.2 1B is 100MB larger and behaves properly.
    ModelInfo(
        name="Llama 3.2 1B Instruct",
        filename="Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        url="https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        size_mb=770,
        description="Smallest model that still holds a conversation properly. For low-end hardware.",
        recommended=False,
    ),
]


class ModelDownloader:
    """Downloads LLM models with progress tracking."""
    
    def __init__(self, models_dir: str):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._cancel_requested = False
        self._current_download: Optional[threading.Thread] = None
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of recommended models for download."""
        return RECOMMENDED_MODELS.copy()
    
    def get_default_model(self) -> ModelInfo:
        """Get the default recommended model."""
        for model in RECOMMENDED_MODELS:
            if model.recommended:
                return model
        return RECOMMENDED_MODELS[0]
    
    def get_installed_models(self) -> List[Tuple[str, str]]:
        """Get list of installed models (name, path)."""
        models = []
        if self.models_dir.exists():
            for f in self.models_dir.glob("*.gguf"):
                models.append((f.stem, str(f)))
        return models
    
    def is_model_installed(self, filename: str) -> bool:
        """Check if a model is already installed."""
        model_path = self.models_dir / filename
        return model_path.exists()
    
    def get_model_path(self, filename: str) -> str:
        """Get full path to a model file."""
        return str(self.models_dir / filename)
    
    MAX_ATTEMPTS = 6
    BACKOFF_SECONDS = 3

    def _open_ranged(self, url: str, offset: int):
        """Open the URL, asking to continue from `offset` bytes in.

        Returns (response, total_size, resuming). `resuming` is False when the
        server ignored the Range header and restarted the body, in which case
        the caller must truncate whatever it already had.
        """
        headers = {"User-Agent": "HearthAI/1.0"}
        if offset:
            headers["Range"] = f"bytes={offset}-"

        response = urllib.request.urlopen(
            urllib.request.Request(url, headers=headers), timeout=60
        )

        resuming = response.status == 206
        if resuming:
            # "bytes 244191483-807694463/807694464" - the total is after the slash
            content_range = response.headers.get("Content-Range", "")
            total = int(content_range.split("/")[-1]) if "/" in content_range else 0
        else:
            total = int(response.headers.get("Content-Length", 0))

        return response, total, resuming

    def download_model(
        self,
        model: ModelInfo,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Download a model in a background thread, resuming where possible.

        A model is a multi-GB download over an ordinary home connection, and
        connections drop. The previous implementation deleted its partial file
        on any error, so a failure at 90% meant starting from zero with no way
        to recover - the worst possible failure on a first run. Partial data is
        now kept and continued with a Range request, and transient network
        errors are retried with a backoff.

        Args:
            model: Model info to download
            progress_callback: Called with (bytes_downloaded, total_bytes)
            complete_callback: Called with model path on success
            error_callback: Called with error message on failure
        """
        self._cancel_requested = False

        def _download():
            dest_path = self.models_dir / model.filename
            temp_path = self.models_dir / f"{model.filename}.part"
            chunk_size = 1024 * 1024
            last_error = None

            for attempt in range(1, self.MAX_ATTEMPTS + 1):
                if self._cancel_requested:
                    break

                offset = temp_path.stat().st_size if temp_path.exists() else 0

                try:
                    response, total_size, resuming = self._open_ranged(model.url, offset)

                    # Server ignored the Range request - start the file again
                    if offset and not resuming:
                        offset = 0

                    downloaded = offset
                    mode = "ab" if offset else "wb"

                    with response, open(temp_path, mode) as f:
                        while True:
                            if self._cancel_requested:
                                break

                            chunk = response.read(chunk_size)
                            if not chunk:
                                break

                            f.write(chunk)
                            downloaded += len(chunk)

                            if progress_callback:
                                progress_callback(downloaded, total_size)

                    if self._cancel_requested:
                        break

                    # A truncated body reads as a clean EOF, so compare against
                    # the expected length rather than trusting the loop exit.
                    if total_size and downloaded < total_size:
                        last_error = (
                            f"Connection closed at {downloaded} of {total_size} bytes"
                        )
                        print(f"[download] {last_error}; attempt {attempt} of {self.MAX_ATTEMPTS}")
                        time.sleep(self.BACKOFF_SECONDS)
                        continue

                    temp_path.replace(dest_path)
                    if complete_callback:
                        complete_callback(str(dest_path))
                    return

                except Exception as e:
                    last_error = str(e)
                    print(f"[download] {last_error}; attempt {attempt} of {self.MAX_ATTEMPTS}")
                    # Keep the partial file: the next attempt resumes from it
                    if attempt < self.MAX_ATTEMPTS:
                        time.sleep(self.BACKOFF_SECONDS)

            if self._cancel_requested:
                # Cancelling is deliberate, so the partial file is discarded
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass
                if error_callback:
                    error_callback("Download cancelled")
                return

            if error_callback:
                kept = " Partial download kept; starting again will resume it." if temp_path.exists() else ""
                error_callback(f"{last_error or 'Download failed'}.{kept}")

        self._current_download = threading.Thread(target=_download, daemon=True)
        self._current_download.start()
    
    def cancel_download(self) -> None:
        """Cancel current download."""
        self._cancel_requested = True


def get_model_downloader() -> ModelDownloader:
    """Get a model downloader instance."""
    return ModelDownloader(str(paths.models_dir()))
