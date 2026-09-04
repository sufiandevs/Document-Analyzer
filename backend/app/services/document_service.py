"""
Document Service - Handles document upload, processing, and management.
"""
import os
import uuid
import logging
from typing import List
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.schemas import DocumentUploadResponse, DocumentInfo, DocumentListResponse, DeleteResponse, DocumentStatus
from app.models.models import DocumentDB
from app.rag.ingestion import process_document
from app.rag.ingestion import delete_document_from_vectorstore

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def save_uploaded_file(file_content: bytes, filename: str) -> str:
    """Save uploaded file to disk and return path."""
    file_id = str(uuid.uuid4())
    safe_filename = Path(filename).name
    file_path = UPLOAD_DIR / f"{file_id}_{safe_filename}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    return str(file_path), file_id

def create_document_record(db: Session, filename: str, file_type: str, file_size: int) -> DocumentDB:
    """Create initial document record in PostgreSQL."""
    doc = DocumentDB(
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        status=DocumentStatus.PENDING
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def process_and_index_document(db: Session, file_path: str, doc_id: str, filename: str) -> dict:
    """Full processing pipeline."""
    try:
        doc = db.query(DocumentDB).filter(DocumentDB.id == doc_id).first()
        if doc:
            doc.status = DocumentStatus.PROCESSING
            db.commit()
        result = process_document(file_path, doc_id, filename)
        if doc:
            doc.status = DocumentStatus.COMPLETED
            doc.chunk_count = result["chunk_count"]
            db.commit()
        return result
    except Exception as e:
        doc = db.query(DocumentDB).filter(DocumentDB.id == doc_id).first()
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            db.commit()
        raise

def upload_document(db: Session, file_content: bytes, filename: str) -> DocumentUploadResponse:
    """Handle document upload: Save → Create DB record → Process and index."""
    ext = Path(filename).suffix.lower()
    if ext not in ['.pdf', '.txt', '.docx', '.doc']:
        raise ValueError(f"Unsupported file type: {ext}")
    
    file_path, file_id = save_uploaded_file(file_content, filename)
    file_size = len(file_content)
    file_type = ext.lstrip('.')
    doc = create_document_record(db, filename, file_type, file_size)
    
    try:
        result = process_and_index_document(db, file_path, doc.id, filename)
        return DocumentUploadResponse(
            id=doc.id,
            filename=filename,
            status=DocumentStatus.COMPLETED,
            message="Document uploaded and indexed successfully",
            chunk_count=result["chunk_count"]
        )
    except Exception as e:
        return DocumentUploadResponse(
            id=doc.id,
            filename=filename,
            status=DocumentStatus.FAILED,
            message=f"Processing failed: {str(e)}"
        )

def list_documents(db: Session) -> DocumentListResponse:
    """List all uploaded documents."""
    docs = db.query(DocumentDB).order_by(DocumentDB.created_at.desc()).all()
    document_list = []
    for doc in docs:
        document_list.append(DocumentInfo(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            status=doc.status,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            metadata=doc.metadata_json
        ))
    return DocumentListResponse(documents=document_list, total=len(document_list))

def delete_document(db: Session, document_id: str) -> DeleteResponse:
    """Delete document from DB and vector store."""
    doc = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
    if not doc:
        return DeleteResponse(success=False, message="Document not found", document_id=document_id)
    try:
        delete_document_from_vectorstore(document_id)
        db.delete(doc)
        db.commit()
        for file in UPLOAD_DIR.glob(f"*{document_id}*"):
            file.unlink(missing_ok=True)
        return DeleteResponse(success=True, message="Document deleted successfully", document_id=document_id)
    except Exception as e:
        return DeleteResponse(success=False, message=f"Delete failed: {str(e)}", document_id=document_id)