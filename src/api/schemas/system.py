"""
System Schemas.

Request and response models for system health and status endpoints.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Liveness check response.
    
    Attributes:
        status: Health status (always "ok" if service is running)
    """
    status: str = Field(..., examples=["ok"])


class VersionResponse(BaseModel):
    """
    Service version information.
    
    Attributes:
        service: Service name
        api_version: API version string
        python_version: Python runtime version
    """
    service: str = Field(..., examples=["research-assistant-api"])
    api_version: str = Field(..., examples=["0.2.0"])
    python_version: str = Field(..., examples=["3.11.7"])


class ReadyResponse(BaseModel):
    """
    Readiness check response.
    
    Attributes:
        status: Overall readiness status ("ok" or "degraded")
        weaviate_ok: Whether Weaviate is reachable
        ollama_ok: Whether Ollama is reachable (None if not configured)
    """
    status: str = Field(..., examples=["ok", "degraded"])
    weaviate_ok: bool
    ollama_ok: Optional[bool] = Field(
        default=None,
        description="Indicates if Ollama is reachable (True/False if configured, null if not configured).",
    )