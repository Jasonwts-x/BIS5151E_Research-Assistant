"""
RAG API Schemas

Request/response models for RAG endpoints.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Query Schemas (Existing)
# ============================================================================


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


# ============================================================================
# Ingestion Schemas (New)
# ============================================================================


class IngestLocalRequest(BaseModel):
    """Request to ingest documents from local filesystem."""

    pattern: str = Field(
        "*",
        description="File pattern to match (e.g., 'arxiv*' for arxiv papers only)",
        examples=["*", "arxiv*", "paper_*.pdf"],
    )


class IngestArxivRequest(BaseModel):
    """Request to ingest papers from ArXiv."""

    query: str = Field(
        ...,
        min_length=1,
        description="ArXiv search query",
        examples=[
            "machine learning",
            "natural language processing",
            "retrieval augmented generation",
        ],
    )
    max_results: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of papers to fetch (1-20)",
    )


class IngestionResponse(BaseModel):
    """Response from ingestion operation."""

    source: str = Field(..., description="Source name (LocalFiles, ArXiv, etc.)")
    documents_loaded: int = Field(..., description="Number of documents fetched")
    chunks_created: int = Field(..., description="Number of chunks created")
    chunks_ingested: int = Field(..., description="Number of chunks written to Weaviate")
    chunks_skipped: int = Field(
        ...,
        description="Number of duplicate chunks skipped",
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of errors encountered (if any)",
    )
    success: bool = Field(..., description="Whether ingestion completed successfully")


# ============================================================================
# Admin Schemas (New)
# ============================================================================


class RAGStatsResponse(BaseModel):
    """RAG index statistics."""

    collection_name: str
    schema_version: str
    document_count: int
    exists: bool
    error: Optional[str] = None


class ResetIndexResponse(BaseModel):
    """Response from index reset operation."""

    success: bool
    message: str
    previous_document_count: Optional[int] = None