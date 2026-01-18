from __future__ import annotations

from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query / research topic.")
    language: str = Field("en", description="Output language (e.g., en, de, fr).")


class RAGQueryResponse(BaseModel):
    query: str
    language: str
    answer: str
    timings: dict[str, float] = Field(
        default_factory=dict,
        description="Best-effort per-stage timings.",
    )
