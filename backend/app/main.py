from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.database import engine, Base
import app.models.domain  # ensures all models register with Base.metadata
from app.api.v1 import health, documents, chat, workflows

logger = logging.getLogger(__name__)
settings = get_settings()

setup_logging(log_level=settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    logger.info("Initializing database and ensuring vector extension...")
    try:
        async with engine.begin() as conn:
            # Enable pgvector if not already enabled
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            # Auto-create tables on clean cloud DBs
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database auto-initialization check skipped/failed: {e}")
    yield


app = FastAPI(
    title="Vitty AI backend",
    description="Backend API for Vitty AI Document Assistant",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if "*" in origins or not origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to Vitty AI API",
        "status": "online",
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
    }