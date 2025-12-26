"""Document loading utilities for various file formats."""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """A chunk of text from a document."""
    content: str
    source: str
    page: Optional[int] = None
    chunk_index: int = 0
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DocumentLoader:
    """Loads and chunks documents from various file formats."""
    
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load(self, file_path: str) -> List[DocumentChunk]:
        """Load a document and return chunks."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = path.suffix.lower()
        
        if ext == ".pdf":
            return self._load_pdf(path)
        elif ext == ".txt":
            return self._load_text(path)
        elif ext == ".md":
            return self._load_text(path)  # Treat markdown as text
        elif ext == ".docx":
            return self._load_docx(path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _load_pdf(self, path: Path) -> List[DocumentChunk]:
        """Load a PDF file."""
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("pypdf is required for PDF support. Install with: pip install pypdf")
        
        reader = PdfReader(path)
        chunks = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            page_chunks = self._chunk_text(text, str(path), page=page_num)
            chunks.extend(page_chunks)
        
        return chunks
    
    def _load_text(self, path: Path) -> List[DocumentChunk]:
        """Load a text or markdown file."""
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        
        return self._chunk_text(text, str(path))
    
    def _load_docx(self, path: Path) -> List[DocumentChunk]:
        """Load a DOCX file."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx is required for DOCX support. Install with: pip install python-docx")
        
        doc = Document(path)
        text = "\n".join([para.text for para in doc.paragraphs])
        
        return self._chunk_text(text, str(path))
    
    def _chunk_text(
        self, 
        text: str, 
        source: str, 
        page: Optional[int] = None
    ) -> List[DocumentChunk]:
        """Split text into overlapping chunks."""
        chunks = []
        
        # Clean up text
        text = text.strip()
        if not text:
            return chunks
        
        # Simple chunking by character count with overlap
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                for sep in [". ", ".\n", "\n\n", "\n", " "]:
                    boundary = text.rfind(sep, start, end)
                    if boundary > start:
                        end = boundary + len(sep)
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append(DocumentChunk(
                    content=chunk_text,
                    source=source,
                    page=page,
                    chunk_index=chunk_index,
                    metadata={
                        "source": source,
                        "page": page,
                        "chunk_index": chunk_index
                    }
                ))
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start <= chunks[-1].chunk_index if chunks else 0:
                start = end
        
        return chunks
    
    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """Check if a file format is supported."""
        return Path(file_path).suffix.lower() in cls.SUPPORTED_EXTENSIONS
