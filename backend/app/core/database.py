from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",
)

async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Alias kept for backwards compatibility
AsyncSessionLocal = async_session_factory

Base = declarative_base()

async def get_db():
    """FastAPI dependency for providing a database session."""
    async with async_session_factory() as session:
        yield session
