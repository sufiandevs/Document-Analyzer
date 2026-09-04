"""
SQLAlchemy ORM Models - Stores document metadata in PostgreSQL (FREE via Docker).
Actual document chunks go to ChromaDB (FREE vector store).
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Float
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

def generate_uuid():
    """Generate a unique ID for documents."""
    return str(uuid.uuid4())

class DocumentDB(Base):
    """PostgreSQL table for document metadata."""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    status = Column(String, default="pending")
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ChatSessionDB(Base):
    """PostgreSQL table for chat sessions."""
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    message_count = Column(Integer, default=0)
    title = Column(String, default="New Chat")

class ChatMessageDB(Base):
    """PostgreSQL table for chat messages."""
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(JSON, default=[])
    retrieval_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())