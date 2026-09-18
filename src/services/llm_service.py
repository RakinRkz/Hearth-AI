"""LLM service for text generation using llama-cpp-python."""

from typing import Generator, List, Dict, Any, Optional, Callable
from threading import Thread
import queue
import os


def get_optimal_gpu_layers(model_path: str, context_length: int = 4096) -> int:
    """
    Determine optimal number of GPU layers based on available VRAM.
    Returns the number of layers that can fit in GPU memory with some buffer.
    
    For GTX 1050 Ti (4GB): 
    - With 4096 context: ~25-32 layers typically fit
    - With 2048 context: All 32+ layers usually fit
    """
    try:
        # Try to get GPU memory info
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.free,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            free_mb, total_mb = map(int, result.stdout.strip().split(','))
            
            # Get model file size as rough estimate of memory needed  
            model_size_mb = os.path.getsize(model_path) / (1024 * 1024)
            
            # KV cache scales significantly with context length
            # Empirically: ~12MB per 1K context for 3-4B parameter models
            kv_cache_estimate = (context_length / 1024) * 12 * 32
            
            # CUDA overhead + compute buffers
            cuda_overhead = 400
            
            # Total reserved
            reserved_mb = cuda_overhead + kv_cache_estimate
            available_for_model = free_mb - reserved_mb
            
            print(f"[GPU] VRAM: {free_mb}MB free / {total_mb}MB total")
            print(f"[GPU] Model size: {model_size_mb:.0f}MB, KV cache estimate: {kv_cache_estimate:.0f}MB")
            print(f"[GPU] Available for model: {available_for_model:.0f}MB")
            
            if available_for_model < model_size_mb * 0.5:
                # Less than half the model fits - might be too fragmented, be conservative
                print(f"[GPU] Limited VRAM, using partial offload")
                # Calculate partial layers
                fraction = available_for_model / model_size_mb
                optimal_layers = max(0, int(fraction * 32))  # Assume 32 layers
            elif available_for_model >= model_size_mb:
                # Full model fits
                optimal_layers = 32  # Cap at typical max layers
                print(f"[GPU] Full model fits in VRAM")
            else:
                # Partial fit
                fraction = available_for_model / model_size_mb
                optimal_layers = int(fraction * 32)
                print(f"[GPU] Partial fit: {optimal_layers} layers ({fraction*100:.0f}%)")
            
            print(f"[GPU] Using {optimal_layers} GPU layers")
            return optimal_layers
            
    except Exception as e:
        print(f"[GPU] Could not detect VRAM: {e}, using CPU")
    
    return 0  # Default to CPU if detection fails


class LLMService:
    """Service for interacting with local LLM via llama-cpp-python."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        context_length: int = 4096,
        gpu_layers: int = -1,  # -1 means auto-detect optimal layers
    ):
        self.model_path = model_path
        self.context_length = context_length
        self.gpu_layers = gpu_layers
        self._llm = None
        self._is_loaded = False
        self._actual_gpu_layers = 0  # Track actual layers used
        self._cancel_generation = False  # Flag to cancel ongoing generation
        self._is_generating = False  # Track if generation is in progress
        # Why the last generation ended: "stop" when the model finished, or
        # "length" when it hit max_tokens. Without this the app cannot tell a
        # finished answer from one severed mid-sentence, and neither can the
        # user - they just see the text stop.
        self.last_finish_reason = None
    
    @property
    def is_loaded(self) -> bool:
        """Check if a model is loaded."""
        return self._is_loaded and self._llm is not None
    
    def load_model(self, model_path: Optional[str] = None) -> None:
        """Load an LLM model with optimal GPU/CPU split."""
        if model_path:
            self.model_path = model_path
        
        if not self.model_path:
            raise ValueError("No model path specified")
        
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "llama-cpp-python is required. Install with: pip install llama-cpp-python"
            )
        
        print(f"Loading model: {self.model_path}")
        
        # Auto-detect optimal GPU layers if set to -1
        if self.gpu_layers == -1:
            self._actual_gpu_layers = get_optimal_gpu_layers(self.model_path, self.context_length)
        else:
            self._actual_gpu_layers = self.gpu_layers
        
        print(f"Using {self._actual_gpu_layers} GPU layers, context length {self.context_length}")
        
        self._llm = Llama(
            model_path=self.model_path,
            n_ctx=self.context_length,
            n_gpu_layers=self._actual_gpu_layers,
            verbose=False,
        )
        
        self._is_loaded = True
        print("Model loaded successfully!")
    
    def unload_model(self) -> None:
        """Unload the current model."""
        if self._llm is not None:
            del self._llm
            self._llm = None
        self._is_loaded = False
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
    ) -> str:
        """Generate a response (non-streaming)."""
        if not self.is_loaded:
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        response = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
        )
        
        self.last_finish_reason = response["choices"][0].get("finish_reason")
        return response["choices"][0]["message"]["content"]
    
    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
    ) -> Generator[str, None, None]:
        """Generate a response with streaming."""
        if not self.is_loaded:
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        response = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
            stream=True,
        )
        
        self.last_finish_reason = None
        for chunk in response:
            choice = chunk["choices"][0]
            if choice.get("finish_reason"):
                self.last_finish_reason = choice["finish_reason"]
            delta = choice.get("delta", {})
            if "content" in delta:
                yield delta["content"]
    
    def generate_async(
        self,
        messages: List[Dict[str, str]],
        callback: Callable[[str], None],
        on_complete: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        **kwargs
    ) -> None:
        """Generate a response asynchronously in a background thread."""
        
        # Cancel any ongoing generation first
        if self._is_generating:
            print("[DEBUG] Cancelling previous generation...")
            self.cancel_generation()
            # Brief wait for cancellation to take effect
            import time
            time.sleep(0.1)
        
        self._cancel_generation = False
        self._is_generating = True
        
        def _generate():
            try:
                print(f"[DEBUG] Starting async generation with {len(messages)} messages")
                token_count = 0
                for token in self.generate_stream(messages, **kwargs):
                    # Check cancellation flag
                    if self._cancel_generation:
                        print(f"[DEBUG] Generation cancelled after {token_count} tokens")
                        break
                    callback(token)
                    token_count += 1
                
                if not self._cancel_generation:
                    print(f"[DEBUG] Generation complete, {token_count} tokens")
                    if on_complete:
                        on_complete()
            except Exception as e:
                if self._cancel_generation:
                    print("[DEBUG] Generation cancelled (exception during cancel)")
                else:
                    print(f"[DEBUG] Generation error: {e}")
                    import traceback
                    traceback.print_exc()
                    if on_error:
                        on_error(e)
            finally:
                self._is_generating = False
        
        thread = Thread(target=_generate, daemon=True)
        thread.start()
    
    def cancel_generation(self) -> None:
        """Cancel ongoing generation."""
        self._cancel_generation = True
    
    @property
    def is_generating(self) -> bool:
        """Check if generation is in progress."""
        return self._is_generating
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not self.is_loaded:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "model_path": self.model_path,
            "context_length": self.context_length,
            "gpu_layers_requested": self.gpu_layers,
            "gpu_layers_actual": self._actual_gpu_layers,
        }
