"""
Chat Service - Orchestrates the full RAG workflow.
Connects the LangGraph agent with database storage.
"""
import time
import uuid
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.agents.graph import get_rag_graph, AgentState
from app.models.schemas import ChatRequest, ChatResponse, ChatHistoryItem, ChatHistoryResponse, Citation
from app.models.models import ChatSessionDB, ChatMessageDB
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_or_create_session(db: Session, session_id: Optional[str] = None) -> str:
    """Get existing session or create new one."""
    if session_id:
        session = db.query(ChatSessionDB).filter(ChatSessionDB.id == session_id).first()
        if session:
            return session_id
    new_id = str(uuid.uuid4())
    new_session = ChatSessionDB(id=new_id)
    db.add(new_session)
    db.commit()
    return new_id

def save_message(db: Session, session_id: str, role: str, content: str, citations: list = None, retrieval_score: float = None):
    """Save a message to the database."""
    message = ChatMessageDB(
        session_id=session_id,
        role=role,
        content=content,
        citations=citations or [],
        retrieval_score=retrieval_score
    )
    db.add(message)
    session = db.query(ChatSessionDB).filter(ChatSessionDB.id == session_id).first()
    if session:
        session.message_count = db.query(ChatMessageDB).filter(
            ChatMessageDB.session_id == session_id
        ).count()
    db.commit()

def process_chat(request: ChatRequest, db: Session) -> ChatResponse:
    """Process a chat question through the full RAG pipeline."""
    start_time = time.time()
    session_id = get_or_create_session(db, request.session_id)
    # Auto-generate title for new sessions on first message
    session = db.query(ChatSessionDB).filter(ChatSessionDB.id == session_id).first()
    if session and session.message_count == 0 and request.question:
        session.title = request.question[:100]
        db.commit()
    save_message(db, session_id, "user", request.question)

    initial_state: AgentState = {
        "question": request.question,
        "rewritten_query": None,
        "documents": [],
        "document_ids": request.document_ids or None,
        "relevance_score": 0.0,
        "answer": "",
        "citations": [],
        "retry_count": 0,
        "max_retries": settings.MAX_RETRIES,
        "query_type": None,
        "needs_retrieval": True,
        "hallucination_check": None,
        "citation_check": None,
        "error": None
    }

    try:
        graph = get_rag_graph()
        final_state = graph.invoke(initial_state)
        processing_time = int((time.time() - start_time) * 1000)

        response = ChatResponse(
            answer=final_state.get("answer", "No answer generated."),
            citations=final_state.get("citations", []),
            retrieval_score=round(final_state.get("relevance_score", 0), 3),
            query_rewritten=final_state.get("rewritten_query") is not None,
            retry_count=final_state.get("retry_count", 0),
            session_id=session_id,
            processing_time_ms=processing_time
        )

        save_message(
            db, session_id, "assistant",
            response.answer,
            [c.model_dump() for c in response.citations],
            response.retrieval_score
        )
        return response

    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        return ChatResponse(
            answer="I apologize, but I encountered an error processing your question. Please try again.",
            citations=[],
            retrieval_score=0.0,
            session_id=session_id,
            processing_time_ms=processing_time
        )

def get_chat_history(db: Session, session_id: str) -> ChatHistoryResponse:
    """Get full chat history for a session."""
    messages = db.query(ChatMessageDB).filter(
        ChatMessageDB.session_id == session_id
    ).order_by(ChatMessageDB.created_at).all()

    history_items = []
    for msg in messages:
        citations = None
        if msg.citations:
            citations = [Citation(**c) for c in msg.citations]
        history_items.append(ChatHistoryItem(
            role=msg.role,
            content=msg.content,
            timestamp=msg.created_at,
            citations=citations
        ))

    return ChatHistoryResponse(
        session_id=session_id,
        messages=history_items,
        total_messages=len(history_items)
    )
def list_chat_sessions(db: Session):
    """Get all chat sessions ordered by most recent."""
    sessions = db.query(ChatSessionDB).order_by(ChatSessionDB.updated_at.desc()).all()
    result = []
    for session in sessions:
        result.append({
            "id": session.id,
            "title": session.title or "New Chat",
            "message_count": session.message_count,
            "created_at": session.created_at,
            "updated_at": session.updated_at
        })
    return result