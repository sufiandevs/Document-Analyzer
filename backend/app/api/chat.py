"""
Chat API Routes

Endpoints:
- POST /chat - Ask a question
- GET /chat/history/{session_id} - Get chat history
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from typing import List
from app.models.schemas import ChatRequest, ChatResponse, ChatHistoryResponse, ChatSessionListResponse
from app.services.chat_service import process_chat, get_chat_history

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Ask a question to the RAG system."""
    try:
        response = process_chat(request, db)
        return response
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Processing failed: {str(e)}")

@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
def chat_history_endpoint(session_id: str, db: Session = Depends(get_db)):
    """Get full chat history for a session."""
    return get_chat_history(db, session_id)
@router.get("/sessions", response_model=ChatSessionListResponse)
def list_sessions_endpoint(db: Session = Depends(get_db)):
    """Get all chat sessions for sidebar."""
    from app.services.chat_service import list_chat_sessions
    sessions = list_chat_sessions(db)
    return ChatSessionListResponse(sessions=sessions, total=len(sessions))