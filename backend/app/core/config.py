"""
CareerPilot AI — Core Configuration
=====================================
What is this?
  Centralized application settings loaded from environment variables.
  We use Pydantic's BaseSettings so every config value is typed and validated.

Why Pydantic BaseSettings?
  - Reads from .env file automatically
  - Type-checks every value at startup
  - Fails fast if a required variable is missing
  - One single source of truth for all config

Interview tip:
  "Why not just use os.getenv() everywhere?"
  Using BaseSettings gives you validation, type coercion, IDE autocompletion,
  and a single place to audit all external config.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "SkillBridge AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://careerpilot:careerpilot@localhost:5432/careerpilot"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Security ─────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-this-to-a-very-long-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── File Upload ───────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: list[str] = ["pdf", "docx", "txt"]
    UPLOAD_DIR: str = "uploads"

    # ── IBM watsonx.ai ────────────────────────────────────────────────────
    # Get these from: https://cloud.ibm.com/
    WATSONX_API_KEY: Optional[str] = None
    WATSONX_PROJECT_ID: Optional[str] = None
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    WATSONX_MODEL_ID: str = "ibm/granite-3-8b-instruct"

    # ── Embeddings ────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # ── RAG ───────────────────────────────────────────────────────────────
    FAISS_INDEX_PATH: str = "rag/vector_store/faiss_index"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 5

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance — import this everywhere
settings = Settings()
