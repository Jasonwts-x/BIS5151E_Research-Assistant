from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])


class VersionResponse(BaseModel):
    service: str = Field(..., examples=["research-assistant-api"])
    api_version: str = Field(..., examples=["0.2.0"])
    python_version: str = Field(..., examples=["3.11.7"])


class ReadyResponse(BaseModel):
    status: str = Field(..., examples=["ok", "degraded"])
    weaviate_ok: bool
    ollama_ok: Optional[bool] = Field(
        default=None,
        description="Indicates if Ollama is reachable (True/False if configured, null if not configured).",
    )
