from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check system health, including database connectivity."""
    health_status = {"status": "ok", "db": "disconnected"}
    try:
        await db.execute(text("SELECT 1"))
        health_status["db"] = "connected"
    except Exception as e:
        health_status["status"] = "error"
        health_status["detail"] = str(e)
    
    return health_status
