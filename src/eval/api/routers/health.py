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
    # TODO: Check database connection
    # TODO: Check TruLens initialization
    
    return {
        "status": "ready",
        "database": "connected",  # TODO: Actual check
        "trulens": "initialized",  # TODO: Actual check
    }