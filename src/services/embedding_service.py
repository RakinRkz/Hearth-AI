"""Embedding service for generating text embeddings."""

from typing import List, Optional


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._is_loaded = False
    
    @property
    def is_loaded(self) -> bool:
        """Check if the embedding model is loaded."""
        return self._is_loaded and self._model is not None
    
    def load_model(self, model_name: Optional[str] = None) -> None:
        """Load the embedding model."""
        if model_name:
            self.model_name = model_name
        
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is required. Install with: pip install sentence-transformers"
            )
        
        print(f"Loading embedding model: {self.model_name}")
        self._model = SentenceTransformer(self.model_name)
        self._is_loaded = True
        print("Embedding model loaded!")
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not self.is_loaded:
            self.load_model()
        
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self.is_loaded:
            self.load_model()
        
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        if not self.is_loaded:
            self.load_model()
        
        return self._model.get_sentence_embedding_dimension()
