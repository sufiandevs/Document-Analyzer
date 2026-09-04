"""
Pydantic Models - Define the shape of all data in the API.
These validate incoming requests and format outgoing responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# ==================== DOCUMENT MODELS ====================

class DocumentStatus(str, Enum):
    """Status of document processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    id: str = Field(..., description="Unique document ID")
    filename: str = Field(..., description="Original filename")
    status: DocumentStatus = Field(..., description="Processing status")
    message: str = Field(default="Document uploaded successfully")
    chunk_count: Optional[int] = Field(default=None, description="Number of chunks created")
    
class DocumentInfo(BaseModel):
    """Information about a stored document."""
    id: str
    filename: str
    file_type: str
    status: DocumentStatus
    chunk_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    """List of all documents."""
    documents: List[DocumentInfo]
    total: int

class DeleteResponse(BaseModel):
    """Response after deleting a document."""
    success: bool
    message: str
    document_id: str

# ==================== CHAT / RAG MODELS ====================

class ChatRequest(BaseModel):
    """User question to the RAG system."""
    question: str = Field(..., min_length=1, max_length=2000, description="User question")
    session_id: Optional[str] = Field(default=None, description="Chat session ID for history")
    top_k: Optional[int] = Field(default=None, ge=1, le=20, description="Override top_k retrieval")
    document_ids: Optional[List[str]] = Field(default=None, description="Limit search to these document IDs")
class Citation(BaseModel):
    """Citation for a document source."""
    document: str = Field(..., description="Document filename")
    page: Optional[int] = Field(default=None, description="Page number")
    chunk_index: Optional[int] = Field(default=None, description="Chunk index")
    score: Optional[float] = Field(default=None, description="Relevance score")
    text: Optional[str] = Field(default=None, description="Retrieved text snippet")

class ChatResponse(BaseModel):
    """AI answer with citations and metadata."""
    answer: str = Field(..., description="Generated answer")
    citations: List[Citation] = Field(default=[], description="Source citations")
    retrieval_score: Optional[float] = Field(default=None, description="Overall relevance score")
    query_rewritten: Optional[bool] = Field(default=False, description="Was query rewritten?")
    retry_count: Optional[int] = Field(default=0, description="Number of retries")
    session_id: str = Field(..., description="Chat session ID")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time")

class ChatHistoryItem(BaseModel):
    """Single chat message in history."""
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime
    citations: Optional[List[Citation]] = None

class ChatHistoryResponse(BaseModel):
    """Full chat history for a session."""
    session_id: str
    messages: List[ChatHistoryItem]
    total_messages: int
class ChatSessionListItem(BaseModel):
    """Single chat session for sidebar list."""
    id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ChatSessionListResponse(BaseModel):
    """List of all chat sessions."""
    sessions: List[ChatSessionListItem]
    total: int
# ==================== HEALTH MODELS ====================

class HealthStatus(BaseModel):
    """System health check response."""
    status: str = Field(..., description="overall status: healthy, degraded, unhealthy")
    timestamp: datetime
    version: str = "1.0.0"
    components: Dict[str, Any] = Field(default={}, description="Individual component status")
    
class ServiceStatus(BaseModel):
    """Individual service health."""
    status: str
    response_time_ms: Optional[int] = None
    error: Optional[str] = None

# ==================== GRAPH STATE (Internal) ====================

class GraphState(BaseModel):
    """LangGraph state - tracks everything through the workflow."""
    question: str = ""
    rewritten_query: Optional[str] = None
    documents: List[Dict[str, Any]] = []
    relevance_score: float = 0.0
    answer: str = ""
    citations: List[Citation] = []
    retry_count: int = 0
    max_retries: int = 3
    query_type: Optional[str] = None
    needs_retrieval: bool = True
    hallucination_check: Optional[bool] = None
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True