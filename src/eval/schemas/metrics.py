"""
Metrics Schemas
Schemas for different types of evaluation metrics.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TruLensMetrics(BaseModel):
    """TruLens evaluation metrics."""

    groundedness: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Groundedness score (0-1)"
    )
    answer_relevance: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Answer relevance score (0-1)"
    )
    context_relevance: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Context relevance score (0-1)"
    )
    citation_quality: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Citation quality score (0-1)"
    )


class GuardrailsResult(BaseModel):
    """Guardrails validation results."""

    passed: bool = Field(..., description="Whether validation passed")
    input_safe: bool = Field(..., description="Input validation passed")
    output_safe: bool = Field(..., description="Output validation passed")
    violations: list[str] = Field(default_factory=list, description="Violations found")
    warnings: list[str] = Field(default_factory=list, description="Warnings")


class PerformanceMetrics(BaseModel):
    """Performance timing and resource metrics."""

    total_time: float = Field(..., description="Total execution time (seconds)")
    rag_time: Optional[float] = Field(
        default=None, description="RAG retrieval time (seconds)"
    )
    agent_times: Optional[Dict[str, float]] = Field(
        default=None, description="Time per agent (seconds)"
    )
    llm_time: Optional[float] = Field(
        default=None, description="Total LLM inference time (seconds)"
    )
    guardrails_time: Optional[float] = Field(
        default=None, description="Guardrails validation time (seconds)"
    )
    evaluation_time: Optional[float] = Field(
        default=None, description="Evaluation computation time (seconds)"
    )
    memory_usage: Optional[Dict[str, Any]] = Field(
        default=None, description="Memory usage statistics"
    )
    token_count: Optional[int] = Field(default=None, description="Total tokens used")


class QualityMetrics(BaseModel):
    """Quality assessment metrics."""

    rouge_scores: Optional[Dict[str, float]] = Field(
        default=None, description="ROUGE scores (rouge-1, rouge-2, rouge-l)"
    )
    bleu_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="BLEU score (0-1)"
    )
    semantic_similarity: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Semantic similarity score (0-1)"
    )
    citation_count: Optional[int] = Field(
        default=None, description="Number of citations in answer"
    )
    answer_length: Optional[int] = Field(
        default=None, description="Answer length in characters"
    )
    sentence_count: Optional[int] = Field(
        default=None, description="Number of sentences in answer"
    )