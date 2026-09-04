"""
Health Check API

Endpoint:
- GET /health - System health status
"""
import time
import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db, get_redis
from app.models.schemas import HealthStatus
from app.rag.retrieval import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=HealthStatus)
async def health_check(db: Session = Depends(get_db)):
    """
    Check system health status.
    
    Returns status of all components:
    - Database (PostgreSQL)
    - Redis (Cache)
    - Vector Store (ChromaDB)
    - LLM (OpenRouter)
    """
    components = {}
    overall_status = "healthy"
    
    # Check PostgreSQL
    try:
        start = time.time()
        db.execute(text("SELECT 1"))
        db_time = int((time.time() - start) * 1000)
        components["database"] = {
            "status": "healthy",
            "response_time_ms": db_time
        }
    except Exception as e:
        components["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "degraded"
    
    # Check Redis
    try:
        start = time.time()
        redis = get_redis()
        await redis.ping()
        redis_time = int((time.time() - start) * 1000)
        components["redis"] = {
            "status": "healthy",
            "response_time_ms": redis_time
        }
    except Exception as e:
        components["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "degraded"
    
    # Check Vector Store
    try:
        start = time.time()
        vs = get_vector_store()
        vs._collection.count()
        vs_time = int((time.time() - start) * 1000)
        components["vector_store"] = {
            "status": "healthy",
            "response_time_ms": vs_time
        }
    except Exception as e:
        components["vector_store"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "degraded"
    
    # Check LLM (just verify API key is set)
    from app.core.config import settings
    if settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY != "sk-or-v1-your-key-here":
        components["llm"] = {"status": "healthy"}
    else:
        components["llm"] = {
            "status": "unhealthy",
            "error": "OpenRouter API key not configured"
        }
        overall_status = "degraded"
    
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow(),
        components=components
    )