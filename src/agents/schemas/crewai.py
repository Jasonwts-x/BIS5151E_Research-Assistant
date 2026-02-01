"""
CrewAI API Schemas.

Request/response models for CrewAI endpoints.

Architecture:
    Shared between API gateway and CrewAI service.
    Provides type-safe request/response handling.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class CrewRunRequest(BaseModel):
    """
    Request to execute CrewAI workflow.
    
    Attributes:
        topic: Research topic or question
        language: Target language code
    """
    
    topic: str = Field(
        ..., 
        description="Research topic or question",
        min_length=3,
        max_length=500
    )
    language: str = Field(
        default="en",
        description="Target language"
    )
    
    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Validate topic string."""
        v = v.strip()
        
        # Check for invalid topics
        if v == "=" or v == "":
            raise ValueError('Topic cannot be empty or just special characters')
        
        # Check minimum length
        if len(v) < 3:
            raise ValueError('Topic must be at least 3 characters long')
        
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        supported = [
            'en',  # English
            'de',  # German
            'fr',  # French
            'es',  # Spanish
            'it',  # Italian
            'pt',  # Portuguese
            'nl',  # Dutch
            'pl',  # Polish
            'ru',  # Russian
            'ja',  # Japanese
            'zh',  # Chinese
            'ko',  # Korean
        ]
       
        v_lower = v.lower()
       
        if v_lower not in supported:
            raise ValueError(
                f'Language {v} not supported. Supported: {supported}'
            )
       
        return v_lower


class CrewRunResponse(BaseModel):
    """
    Response from CrewAI workflow.
    
    Attributes:
        topic: Original research topic
        language: Language code
        answer: Generated research summary
        evaluation: Evaluation metrics
    """
    
    topic: str = Field(..., description="Original research topic")
    language: str = Field(..., description="Language code")
    answer: str = Field(..., description="Generated research summary")

    evaluation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Evaluation metrics (TruLens, Guardrails, Performance)"
    )


# ==============================================================================
# Async Job Tracking Schemas
# ==============================================================================


class CrewAsyncRunResponse(BaseModel):
    """
    Response from async crew job submission.
    
    Attributes:
        job_id: Job ID for tracking
        status: Initial status
        message: Human-readable message
    """
    
    job_id: str = Field(..., description="Job ID for tracking execution")
    status: str = Field(..., description="Initial status (always 'pending')")
    message: str = Field(..., description="Human-readable message")


class CrewStatusResponse(BaseModel):
    """
    Crew job status response.
    
    Attributes:
        job_id: Job identifier
        status: Current status
        topic: Research topic
        language: Target language
        progress: Progress from 0.0 to 1.0
        created_at: Creation timestamp
        started_at: Start timestamp
        completed_at: Completion timestamp
        result: Final result (if completed)
        error: Error message (if failed)
        evaluation: Evaluation metrics (if completed)
    """
    
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(
        ..., 
        description="Job status: pending, running, completed, failed"
    )
    topic: str = Field(..., description="Research topic")
    language: str = Field(..., description="Target language")
    progress: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Progress from 0.0 to 1.0"
    )
    created_at: str = Field(..., description="Job creation timestamp (ISO format)")
    started_at: str | None = Field(None, description="Job start timestamp")
    completed_at: str | None = Field(None, description="Job completion timestamp")
    result: str | None = Field(None, description="Final result if completed")
    error: str | None = Field(None, description="Error message if failed")

    evaluation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Evaluation metrics (only present when status=completed)"
    )