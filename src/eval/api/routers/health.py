"""
Health Check Router
Service health and status endpoints.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Health check for evaluation service",
)
def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "evaluation",
    }


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
)
def readiness_check():
    """Check if service is ready to accept requests."""
    
    # ✨ IMPROVED: Actually check database
    try:
        from ...database import get_database
        db = get_database()
        db_healthy = db.health_check()
    except Exception as e:
        logger.error("Database check failed: %s", e)
        db_healthy = False
    
    if not db_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    return {
        "status": "ready",
        "database": "connected",
        "trulens": "initialized",
    }