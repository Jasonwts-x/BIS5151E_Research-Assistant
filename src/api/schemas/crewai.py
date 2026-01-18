from __future__ import annotations

from pydantic import BaseModel, Field


class CrewRunRequest(BaseModel):
    """Request schema for running CrewAI workflow."""

    topic: str = Field(
        ...,
        min_length=1,
        description="Research topic or question to investigate",
        examples=["What is digital transformation?", "Explain RAG systems"],
    )
    language: str = Field(
        "en",
        description="Output language (currently only 'en' supported; translation in Step H)",
        examples=["en", "de", "fr"],
    )


class CrewRunResponse(BaseModel):
    """Response schema for CrewAI workflow execution."""

    topic: str = Field(..., description="The research topic that was processed")
    language: str = Field(..., description="The requested output language")
    answer: str = Field(
        ...,
        description="Final fact-checked summary from the crew workflow"
    )


# ==============================================================================
# Async Job Tracking Schemas (Placeholder for Future Implementation)
# ==============================================================================
# NOTE: These schemas are placeholders for future async job execution.
# Currently not used - synchronous execution only (/crewai/run endpoint).
# TODO: Implement in a future step when async job tracking is needed.
# ==============================================================================


class CrewRunAsyncResponse(BaseModel):
    """
    Async crew execution response (job started).
    
    **Placeholder for future async implementation.**
    """
    job_id: str = Field(..., description="Job ID for tracking execution")
    status: str = Field(..., description="Initial status (e.g., 'pending')")
    message: str = Field(..., description="Human-readable message")


class CrewStatusResponse(BaseModel):
    """
    Crew job status response.
    
    **Placeholder for future async implementation.**
    """
    job_id: str
    status: str = Field(
        ..., 
        description="Job status: pending, running, completed, failed"
    )
    progress: float | None = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Progress 0-1"
    )
    result: str | None = Field(
        None, 
        description="Final result if completed"
    )
    error: str | None = Field(
        None, 
        description="Error message if failed"
    )
    agents_used: list[str] = Field(
        default_factory=list,
        description="List of agents that executed in the workflow"
    )
    task_outputs: dict[str, str] = Field(
        default_factory=dict,
        description="Outputs from individual tasks"
    )