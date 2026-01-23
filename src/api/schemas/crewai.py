"""
CrewAI API Schemas

Request/response models for CrewAI endpoints.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CrewRunRequest(BaseModel):
    """Request to run CrewAI workflow."""
    
    topic: str = Field(
        ..., 
        min_length=3,
        max_length=500,
        description="Research topic or question"
    )
    language: str = Field(
        "en",
        description="Target language (only 'en' currently supported)"
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
        supported = ['en']  # Extend when translation is implemented
        if v not in supported:
            raise ValueError(f'Language {v} not supported. Supported: {supported}')
        return v


class CrewRunResponse(BaseModel):
    """Response from CrewAI workflow."""
    
    topic: str
    language: str
    answer: str


# ==============================================================================
# Async Job Tracking Schemas (Placeholder for Future Implementation)
# ==============================================================================
# NOTE: These schemas are placeholders for future async job execution.
# Currently not used - synchronous execution only (/crewai/run endpoint).
# TODO: Implement in a future step when async job tracking is needed.
# ==============================================================================


# class CrewRunAsyncResponse(BaseModel):
#     """
#     Async crew execution response (job started).
    
#     **Placeholder for future async implementation.**
#     """
#     job_id: str = Field(..., description="Job ID for tracking execution")
#     status: str = Field(..., description="Initial status (e.g., 'pending')")
#     message: str = Field(..., description="Human-readable message")


# class CrewStatusResponse(BaseModel):
#     """
#     Crew job status response.
    
#     **Placeholder for future async implementation.**
#     """
#     job_id: str
#     status: str = Field(
#         ..., 
#         description="Job status: pending, running, completed, failed"
#     )
#     progress: float | None = Field(
#         None, 
#         ge=0.0, 
#         le=1.0, 
#         description="Progress 0-1"
#     )
#     result: str | None = Field(
#         None, 
#         description="Final result if completed"
#     )
#     error: str | None = Field(
#         None, 
#         description="Error message if failed"
#     )
#     agents_used: list[str] = Field(
#         default_factory=list,
#         description="List of agents that executed in the workflow"
#     )
#     task_outputs: dict[str, str] = Field(
#         default_factory=dict,
#         description="Outputs from individual tasks"
#     )