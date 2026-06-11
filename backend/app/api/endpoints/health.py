"""
Health check endpoints.
"""

from fastapi import APIRouter
from app.config import settings
from app.core.app_modes import mode_manager

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
        "mode": mode_manager.current_mode.value,
    }


@router.get("/ready")
async def readiness_check():
    """Readiness probe."""
    return {
        "ready": True,
        "mode": mode_manager.current_mode.value,
        "data_source": mode_manager.data_source.value,
    }
