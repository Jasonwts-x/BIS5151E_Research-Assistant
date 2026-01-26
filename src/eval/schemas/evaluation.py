"""
Evaluation Request/Response Schemas
Core schemas for evaluation API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    """Request to evaluate a query/answer pair."""

    query: str = Field(..., description="User query")
    answer: str = Field(..., description="Generated answer")
    context: str = Field(..., description="Retrieved context")
    language: str = Field(default="en", description="Language code")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class EvaluationSummary(BaseModel):
    """Summary of evaluation results."""

    passed: bool = Field(..., description="Whether evaluation passed all checks")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall score (0-1)")
    issues: List[str] = Field(default_factory=list, description="Issues found")
    warnings: List[str] = Field(default_factory=list, description="Warnings")


class EvaluationResponse(BaseModel):
    """Complete evaluation results."""

    record_id: str = Field(..., description="Unique evaluation record ID")
    timestamp: datetime = Field(..., description="Evaluation timestamp")
    query: str = Field(..., description="Evaluated query")
    answer_length: int = Field(..., description="Answer length in characters")

    summary: EvaluationSummary = Field(..., description="Evaluation summary")

    trulens: Optional[Dict[str, Any]] = Field(
        default=None, description="TruLens metrics (groundedness, relevance)"
    )
    guardrails: Optional[Dict[str, Any]] = Field(
        default=None, description="Guardrails validation results"
    )
    performance: Optional[Dict[str, Any]] = Field(
        default=None, description="Performance metrics (timing, resources)"
    )
    quality: Optional[Dict[str, Any]] = Field(
        default=None, description="Quality metrics (ROUGE, BLEU, etc.)"
    )


class LeaderboardEntry(BaseModel):
    """Single entry in evaluation leaderboard."""

    record_id: str
    timestamp: datetime
    query: str
    overall_score: float
    groundedness: Optional[float] = None
    answer_relevance: Optional[float] = None
    context_relevance: Optional[float] = None
    total_time: Optional[float] = None
    passed_guardrails: bool = True


class LeaderboardResponse(BaseModel):
    """Leaderboard of all evaluations."""

    total_records: int
    entries: List[LeaderboardEntry]
    filters: Optional[Dict[str, Any]] = None