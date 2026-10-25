from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://vitty:vitty_password@localhost:5432/vitty_db"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://vitty:vitty_password@localhost:5432/vitty_db"

    # Object Storage (local filesystem for POC)
    STORAGE_DIR: str = "./storage/documents"

    # LLM
    LLM_PROVIDER: str = "ollama"  # ollama | groq | gemini | openai
    LLM_MODEL: str = "llama3"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Embeddings
    EMBEDDING_PROVIDER: str = "ollama"  # ollama | gemini | openai
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIMENSIONS: int = 768

    # CORS
    CORS_ORIGINS: str = "*"

    # Auth
    JWT_SECRET: str = "super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24  # 24 hours

    # Limits
    MAX_FILE_SIZE_MB: int = 50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
