"""
Research API Schemas.

Schemas for the primary research workflow endpoints.
These provide a clean, user-friendly interface for research queries.

Architecture Note:
    These schemas are designed for end users and abstract away
    the underlying RAG + CrewAI + Evaluation complexity.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResearchQueryRequest(BaseModel):
    """
    Request for research query.
    
    Attributes:
        query: Research question or topic
        language: Target language for the summary (default: English)
        top_k: Number of documents to retrieve from RAG (default: 5)
        enable_evaluation: Whether to include evaluation metrics (default: True)
    """
    query: str = Field(
        ...,
        description="Research question or topic to investigate",
        min_length=3,
        max_length=500,
        examples=[
            "What is retrieval augmented generation?",
            "Explain transformer neural networks",
            "Recent advances in large language models",
        ],
    )
    language: str = Field(
        default="en",
        description="Target language code (en, de, fr, es, etc.)",
        pattern="^[a-z]{2}$",
        examples=["en", "de", "fr", "es"],
    )
    top_k: Optional[int] = Field(
        default=5,
        description="Number of most relevant documents to retrieve",
        ge=1,
        le=20,
    )
    enable_evaluation: Optional[bool] = Field(
        default=True,
        description="Include evaluation metrics in response",
    )


class ResearchQueryResponse(BaseModel):
    """
    Response from research query.
    
    Attributes:
        query: Original research question
        summary: Generated research summary with citations
        language: Language of the summary
        sources: List of source documents used
        retrieved_chunks: Number of document chunks retrieved
        evaluation: Optional evaluation metrics (performance, quality, guardrails)
        metadata: Additional metadata about the execution
    """
    query: str = Field(..., description="Original research question")
    summary: str = Field(..., description="Generated research summary with citations")
    language: str = Field(..., description="Language of the summary")
    sources: List[str] = Field(
        ...,
        description="List of source documents used in the summary",
    )
    retrieved_chunks: int = Field(
        ...,
        description="Number of document chunks retrieved from RAG",
    )
    evaluation: Optional[Dict[str, Any]] = Field(
        None,
        description="Evaluation metrics (performance, TruLens, guardrails)",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional execution metadata",
    )


class ResearchAsyncResponse(BaseModel):
    """
    Response from async research query submission.
    
    Attributes:
        job_id: Unique job identifier for status tracking
        status: Current job status (pending, running, completed, failed)
        message: Human-readable status message
        query: Original research question
    """
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(
        ...,
        description="Job status (pending, running, completed, failed)",
    )
    message: str = Field(..., description="Human-readable status message")
    query: Optional[str] = Field(None, description="Original research question")


class ResearchStatusResponse(BaseModel):
    """
    Research job status and results.
    
    Attributes:
        job_id: Unique job identifier
        status: Current job status
        progress: Progress percentage (0.0-1.0)
        created_at: Job creation timestamp
        started_at: Job start timestamp (if started)
        completed_at: Job completion timestamp (if completed)
        result: Research result (if completed)
        error: Error message (if failed)
    """
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(
        ...,
        description="Job status (pending, running, completed, failed)",
    )
    progress: float = Field(
        ...,
        description="Progress percentage (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )
    created_at: str = Field(..., description="Job creation timestamp (ISO format)")
    started_at: Optional[str] = Field(
        None,
        description="Job start timestamp (ISO format)",
    )
    completed_at: Optional[str] = Field(
        None,
        description="Job completion timestamp (ISO format)",
    )
    result: Optional[ResearchQueryResponse] = Field(
        None,
        description="Research result (available when status is 'completed')",
    )
    error: Optional[str] = Field(
        None,
        description="Error message (available when status is 'failed')",
    )