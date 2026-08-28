"""REST endpoints for document management."""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from pathlib import Path
from datetime import datetime
import shutil
import sys

# Add parent to path for imports
src_dir = Path(__file__).parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from api.schemas import DocumentInfo, DocumentUploadResponse
from api.dependencies import get_rag_service
from utils.config import get_config
from utils import paths

router = APIRouter()


def get_documents_dir() -> Path:
    """Get the documents directory path."""
    config = get_config()
    return paths.documents_dir()


@router.get("", response_model=List[DocumentInfo])
async def list_documents():
    """List all uploaded documents."""
    rag_service = get_rag_service()
    documents_dir = get_documents_dir()
    
    documents = []
    
    # Get indexed files from RAG service if available
    indexed_files = {}
    if rag_service:
        try:
            rag_service._ensure_initialized()
            indexed_files = rag_service._indexed_files
        except Exception:
            pass
    
    # List files in documents directory
    if documents_dir.exists():
        for file_path in documents_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.txt', '.md', '.docx']:
                file_id = file_path.stem
                indexed_info = indexed_files.get(str(file_path), {})
                
                documents.append(DocumentInfo(
                    id=file_id,
                    filename=file_path.name,
                    file_path=str(file_path),
                    chunk_count=indexed_info.get("num_chunks", 0),
                    indexed_at=datetime.fromtimestamp(file_path.stat().st_mtime),
                ))
    
    return documents


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document."""
    rag_service = get_rag_service()
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.txt', '.md', '.docx'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save file to documents directory
    documents_dir = get_documents_dir()
    documents_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = documents_dir / file.filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Index the document
    try:
        chunk_count = rag_service.add_document(str(file_path))
        
        return DocumentUploadResponse(
            success=True,
            filename=file.filename,
            chunk_count=chunk_count,
            message=f"Successfully indexed {chunk_count} chunks"
        )
    except Exception as e:
        # Clean up file if indexing fails
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to index document: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and remove from index."""
    rag_service = get_rag_service()
    documents_dir = get_documents_dir()
    
    # Find the document file
    document_file = None
    for file_path in documents_dir.iterdir():
        if file_path.stem == document_id:
            document_file = file_path
            break
    
    if not document_file:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Remove from vector store if RAG service available
    if rag_service:
        try:
            rag_service.remove_document(str(document_file))
        except Exception:
            pass  # Continue even if removal from index fails
    
    # Delete the file
    try:
        document_file.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
    
    return {"success": True, "message": "Document deleted"}
