"""
Main FastAPI Application

Production-style API with:
- Pydantic validation
- Error handling
- Logging
- CORS
- API documentation
- Health checks
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.database import init_db
from app.api import documents, chat, health

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting up Advanced RAG System...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    yield
    
    logger.info("Shutting down...")

# Create FastAPI app
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="""
        Production-Ready Multi-Agent RAG System
        
        Features:
        - Document ingestion (PDF, TXT, DOCX)
        - Semantic retrieval with MMR
        - Cross-encoder re-ranking
        - LangGraph agentic workflow
        - Hallucination detection
        - Citation verification
        
        Built with: LangChain, LangGraph, FastAPI, ChromaDB, HuggingFace
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # CORS - Allow frontend to communicate with backend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.include_router(health.router)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
            }
        )
    
    # Root endpoint
    @app.get("/")
    def root():
        return {
            "message": "Advanced RAG System API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    
    return app

app = create_app()

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Production-Ready Multi-Agent RAG System",
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi