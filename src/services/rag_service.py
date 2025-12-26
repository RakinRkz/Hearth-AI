"""RAG (Retrieval-Augmented Generation) service."""

from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import json
import sys

from .embedding_service import EmbeddingService

# Add parent to path for sibling imports
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from utils.document_loader import DocumentLoader, DocumentChunk


class RAGService:
    """Service for RAG operations using ChromaDB."""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        persist_directory: str = "data/vectorstore",
        collection_name: str = "documents",
    ):
        self.embedding_service = embedding_service
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._document_loader = DocumentLoader()
        self._indexed_files: Dict[str, Dict[str, Any]] = {}
    
    def _ensure_initialized(self) -> None:
        """Ensure ChromaDB is initialized."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
            except ImportError:
                raise ImportError(
                    "chromadb is required. Install with: pip install chromadb"
                )
            
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            self._load_indexed_files()
    
    def _load_indexed_files(self) -> None:
        """Load the list of indexed files from metadata."""
        metadata_path = Path(self.persist_directory) / "indexed_files.json"
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                self._indexed_files = json.load(f)
    
    def _save_indexed_files(self) -> None:
        """Save the list of indexed files to metadata."""
        metadata_path = Path(self.persist_directory) / "indexed_files.json"
        with open(metadata_path, "w") as f:
            json.dump(self._indexed_files, f, indent=2)
    
    def add_document(self, file_path: str) -> int:
        """Add a document to the vector store."""
        self._ensure_initialized()
        
        # Load and chunk the document
        chunks = self._document_loader.load(file_path)
        
        if not chunks:
            return 0
        
        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.embed_batch(texts)
        
        # Prepare data for ChromaDB
        ids = [f"{Path(file_path).stem}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": chunk.source,
                "page": chunk.page or 0,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ]
        
        # Add to collection
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        
        # Track indexed file
        self._indexed_files[file_path] = {
            "num_chunks": len(chunks),
            "ids": ids,
        }
        self._save_indexed_files()
        
        return len(chunks)
    
    def remove_document(self, file_path: str) -> bool:
        """Remove a document from the vector store."""
        self._ensure_initialized()
        
        if file_path not in self._indexed_files:
            return False
        
        ids = self._indexed_files[file_path]["ids"]
        self._collection.delete(ids=ids)
        
        del self._indexed_files[file_path]
        self._save_indexed_files()
        
        return True
    
    def query(
        self, 
        query_text: str, 
        top_k: int = 4
    ) -> List[Tuple[str, Dict[str, Any], float]]:
        """Query the vector store for relevant chunks."""
        self._ensure_initialized()
        
        if self._collection.count() == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed(query_text)
        
        # Query ChromaDB
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                # Convert distance to similarity score (cosine)
                similarity = 1 - dist
                formatted.append((doc, meta, similarity))
        
        return formatted
    
    def get_context_for_query(
        self, 
        query_text: str, 
        top_k: int = 4
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Get formatted context and sources for a query."""
        results = self.query(query_text, top_k)
        
        if not results:
            return "", []
        
        context_parts = []
        sources = []
        
        for i, (doc, meta, score) in enumerate(results, 1):
            context_parts.append(f"[{i}] {doc}")
            sources.append({
                "title": Path(meta["source"]).name,
                "content": doc[:200] + "..." if len(doc) > 200 else doc,
                "page": meta.get("page"),
                "score": score,
            })
        
        context = "\n\n".join(context_parts)
        return context, sources
    
    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        """Get list of indexed documents."""
        self._ensure_initialized()
        
        return [
            {
                "path": path,
                "name": Path(path).name,
                "num_chunks": info["num_chunks"],
            }
            for path, info in self._indexed_files.items()
        ]
    
    def clear(self) -> None:
        """Clear all documents from the vector store."""
        self._ensure_initialized()
        
        # Delete all items
        if self._collection.count() > 0:
            all_ids = self._collection.get()["ids"]
            if all_ids:
                self._collection.delete(ids=all_ids)
        
        self._indexed_files = {}
        self._save_indexed_files()
