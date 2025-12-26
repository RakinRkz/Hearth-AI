"""Embedding service for generating text embeddings."""

from typing import List, Optional


class EmbeddingService:
    """Service for generating text embeddings using fastembed (ONNX-based).
    
    Uses fastembed which is lighter than sentence-transformers and doesn't
    conflict with llama-cpp-python's CUDA libraries.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Map common model names to fastembed model names
        self._model_map = {
            "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
            "all-mpnet-base-v2": "sentence-transformers/all-mpnet-base-v2",
        }
        self.model_name = self._model_map.get(model_name, model_name)
        self._model = None
        self._is_loaded = False
    
    @property
    def is_loaded(self) -> bool:
        """Check if the embedding model is loaded."""
        return self._is_loaded and self._model is not None
    
    def load_model(self, model_name: Optional[str] = None) -> None:
        """Load the embedding model."""
        if model_name:
            self.model_name = self._model_map.get(model_name, model_name)
        
        try:
            from fastembed import TextEmbedding
        except ImportError:
            raise ImportError(
                "fastembed is required. Install with: pip install fastembed"
            )
        
        print(f"Loading embedding model: {self.model_name}")
        self._model = TextEmbedding(model_name=self.model_name)
        self._is_loaded = True
        print("Embedding model loaded!")
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not self.is_loaded:
            self.load_model()
        
        # fastembed returns a generator, convert to list
        embeddings = list(self._model.embed([text]))
        return embeddings[0].tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self.is_loaded:
            self.load_model()
        
        embeddings = list(self._model.embed(texts))
        return [e.tolist() for e in embeddings]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        if not self.is_loaded:
            self.load_model()
        
        # Get dimension by embedding a test text
        test_embedding = self.embed("test")
        return len(test_embedding)
