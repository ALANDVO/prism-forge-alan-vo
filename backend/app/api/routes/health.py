from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Health check endpoint with database connectivity verification."""
    settings = get_settings()
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "version": settings.app_version,
        "environment": settings.environment,
        "database": db_status,
        "demo_mode": settings.is_demo_allowed,
    }


@router.get("/health/ready")
async def readiness_check() -> dict:
    """Kubernetes-style readiness probe."""
    return {"ready": True}