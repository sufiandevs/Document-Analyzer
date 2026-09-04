"""
Application Configuration - Central place for all settings.
Reads from environment variables with sensible defaults.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """All app settings loaded from .env file or environment variables."""
    
    # App
    APP_NAME: str = "Advanced RAG System"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # API Keys
    OPENROUTER_API_KEY: str = "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"
    HUGGINGFACE_API_KEY: str = "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"
    
    # LLM (OpenRouter - FREE Meta Llama 3.8B)
    LLM_MODEL: str = "meta-llama/llama-3.1-8b-instruct"
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1024
    
    # Embeddings (FREE - HuggingFace Local)
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Reranker (FREE - HuggingFace Local)
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    
    # Database
    DATABASE_URL: str = "postgresql://raguser:ragpassword@localhost:5432/ragdb"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Chroma Vector DB
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # RAG Settings
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 10
    TOP_K_RERANK: int = 5
    SIMILARITY_THRESHOLD: float = 0.1
    MAX_RETRIES: int = 1
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings()