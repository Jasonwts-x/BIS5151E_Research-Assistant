from __future__ import annotations

from fastapi import HTTPException, status


def internal_server_error(detail: str = "Internal server error.") -> HTTPException:
    """
    Minimal error helper used by routers.

    Later upgrades (optional):
    - define an ErrorResponse schema (code/message/request_id)
    - add global exception handlers in server.py to normalize error shape
    """
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
    )


def service_unavailable(detail: str = "Service unavailable.") -> HTTPException:
    """
    Use when a required downstream dependency is not reachable.
    """
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Placeholders for future improvements (NOT implemented yet)
# ---------------------------------------------------------------------------
# - class ErrorResponse(BaseModel): ...
# - def bad_request(...), not_found(...), service_unavailable(...)
# - FastAPI exception handlers that return ErrorResponse consistently
