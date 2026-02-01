"""
Ollama Schemas.

Request and response models for Ollama service interaction.
Covers model management, service information, and chat completion.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Ollama Model Information
# ============================================================================


class OllamaModel(BaseModel):
    """
    Represents a single Ollama model.
    
    Attributes:
        name: Model name (e.g., "qwen2.5:3b")
        size: Model size in bytes
        digest: Model digest/hash for verification
        modified_at: Last modification timestamp
        details: Additional model metadata
    """

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
        """Convert datetime objects to ISO string for JSON serialization."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @field_validator('details', mode='before')
    @classmethod
    def convert_details(cls, v):
        """Convert ModelDetails object to dict for JSON serialization."""
        if hasattr(v, '__dict__'):
            return v.__dict__
        return v or {}


class OllamaModelsResponse(BaseModel):
    """
    Response for listing available Ollama models.
    
    Attributes:
        models: List of available models with metadata
    """
    models: List[OllamaModel] = Field(default_factory=list)


# ============================================================================
# Ollama Service Information
# ============================================================================


class OllamaInfoResponse(BaseModel):
    """
    Response for Ollama service information.
    
    Attributes:
        status: Service health status ("healthy" or "unhealthy")
        host: Ollama service host URL
        configured_model: Model configured in application settings
        available_models: List of model names currently available
    """
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
    """
    Request to pull/download a model.
    
    Attributes:
        model: Model name to download
    """
    model: str = Field(..., examples=["qwen3:4b", "llama3:8b"])


class OllamaPullResponse(BaseModel):
    """
    Response for model pull operation.
    
    Attributes:
        model: Model name being pulled
        status: Pull status ("started", "completed", "failed")
        message: Optional status message
    """
    model: str
    status: str = Field(..., examples=["started", "completed", "failed"])
    message: Optional[str] = None


# ============================================================================
# Chat Completion
# ============================================================================


class OllamaChatMessage(BaseModel):
    """
    Single message in chat conversation.
    
    Attributes:
        role: Message role ("user", "assistant", "system")
        content: Message text content
    """
    role: str = Field(..., examples=["user", "assistant", "system"])
    content: str


class OllamaChatRequest(BaseModel):
    """
    Request for chat completion via Ollama.
    
    Attributes:
        model: Model to use (defaults to configured model if not specified)
        messages: List of conversation messages
        stream: Whether to stream the response
        temperature: Sampling temperature for generation (0.0-2.0)
    """
    model: Optional[str] = Field(
        None, description="Model to use (defaults to configured model)"
    )
    messages: List[OllamaChatMessage]
    stream: bool = Field(False, description="Whether to stream the response")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)


class OllamaChatResponse(BaseModel):
    """
    Response from chat completion.
    
    Attributes:
        model: Model that generated the response
        message: Generated assistant message
        done: Whether generation is complete
    """
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