"""
API Error Handlers.

Minimal error helper functions used by routers for consistent error responses.

Architecture Note:
    Currently provides basic HTTPException wrappers.
    Future upgrades may include:
        - ErrorResponse schema (code/message/request_id)
        - Global exception handlers in server.py to normalize error shape
        - Structured logging for errors
"""
from __future__ import annotations

from fastapi import HTTPException, status


def internal_server_error(detail: str = "Internal server error.") -> HTTPException:
    """
    Create internal server error response (500).
    
    Args:
        detail: Error message for user
        
    Returns:
        HTTPException with 500 status code
    """
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
    )


def service_unavailable(detail: str = "Service unavailable.") -> HTTPException:
    """
    Create service unavailable error response (503).
    
    Use when a required downstream dependency is not reachable.
    
    Args:
        detail: Error message for user
        
    Returns:
        HTTPException with 503 status code
    """
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=detail,
    )
