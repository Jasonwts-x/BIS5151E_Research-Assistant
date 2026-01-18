from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Ollama Model Information
# ============================================================================


class OllamaModel(BaseModel):
    """Represents a single Ollama model."""

    name: str = Field(..., description="Model name")
    size: Optional[int] = Field(None, description="Model size in bytes")
    digest: Optional[str] = Field(None, description="Model digest/hash")
    modified_at: Optional[str] = Field(None, description="Last modification timestamp")
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional model metadata"
    )

    @field_validator('modified_at', mode='before')
    @classmethod
    def convert_datetime(cls, v):
        """Convert datetime objects to ISO string."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    
    @field_validator('details', mode='before')
    @classmethod
    def convert_details(cls, v):
        """Convert ModelDetails object to dict."""
        if hasattr(v, '__dict__'):
            return v.__dict__
        return v or {}


class OllamaModelsResponse(BaseModel):
    """Response for listing available Ollama models."""

    models: List[OllamaModel] = Field(default_factory=list)


# ============================================================================
# Ollama Service Information
# ============================================================================


class OllamaInfoResponse(BaseModel):
    """Response for Ollama service information."""

    status: str = Field(..., examples=["healthy", "unhealthy"])
    host: str = Field(..., description="Ollama service host URL")
    configured_model: str = Field(..., description="Model configured in app settings")
    available_models: List[str] = Field(
        default_factory=list, description="List of available model names"
    )


# ============================================================================
# Model Pull (Placeholder for Step G - QoL)
# ============================================================================


class OllamaPullRequest(BaseModel):
    """Request to pull/download a model."""

    model: str = Field(..., examples=["qwen3:4b", "llama3:8b"])


class OllamaPullResponse(BaseModel):
    """Response for model pull operation."""

    model: str
    status: str = Field(..., examples=["started", "completed", "failed"])
    message: Optional[str] = None


# ============================================================================
# Chat Completion (Placeholder for Step D - CrewAI Integration)
# ============================================================================


class OllamaChatMessage(BaseModel):
    """Single message in chat conversation."""

    role: str = Field(..., examples=["user", "assistant", "system"])
    content: str


class OllamaChatRequest(BaseModel):
    """Request for chat completion via Ollama."""

    model: Optional[str] = Field(
        None, description="Model to use (defaults to configured model)"
    )
    messages: List[OllamaChatMessage]
    stream: bool = Field(False, description="Whether to stream the response")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)


class OllamaChatResponse(BaseModel):
    """Response from chat completion."""

    model: str
    message: OllamaChatMessage
    done: bool = True


# ============================================================================
# TODO: Implement in Step D (CrewAI Integration)
# - Add streaming support for chat endpoint
# - Add tool/function calling schemas if needed by CrewAI
# ============================================================================

# ============================================================================
# TODO: Implement in Step G (QoL)
# - Add model deletion endpoint schema
# - Add model copy/rename schemas
# - Add embeddings endpoint schema (if needed)
# ============================================================================