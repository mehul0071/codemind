from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.sessions import get_db
from app.config import settings

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "disconnected"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "db": db_status,
                "error": str(e),
                "model": settings.MODEL_NAME,
            },
        )

    return {
        "status": "ok",
        "db": db_status,
        "model": settings.MODEL_NAME,
        "embedding_model": settings.EMBEDDING_MODEL,
    }
