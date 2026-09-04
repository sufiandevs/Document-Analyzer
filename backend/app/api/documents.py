"""
Document API Routes (Part 4 - 10 Marks)

Endpoints:
- POST /documents/upload - Upload a document
- GET /documents - List all documents
- DELETE /documents/{id} - Delete a document
"""
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.document_service import upload_document, list_documents, delete_document
from app.models.schemas import DocumentUploadResponse, DocumentListResponse, DeleteResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_endpoint(
    file: UploadFile = File(..., description="PDF, TXT, or DOCX file"),
    db: Session = Depends(get_db)
):
    """Upload a document for indexing."""
    filename = file.filename or "unknown"
    if not any(filename.lower().endswith(ext) for ext in ['.pdf', '.txt', '.docx', '.doc']):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF, TXT, and DOCX files are supported")
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 50MB)")
        result = upload_document(db, content, filename)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}")

@router.get("", response_model=DocumentListResponse)
def list_documents_endpoint(db: Session = Depends(get_db)):
    """List all uploaded documents with their status."""
    return list_documents(db)

@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document_endpoint(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and all its indexed chunks."""
    result = delete_document(db, document_id)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.message)
    return result