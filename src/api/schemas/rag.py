"""
RAG API Schemas.

Request/response models for RAG endpoints (ingestion, query, stats, admin).
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Query Schemas
# ============================================================================


class RAGQueryRequest(BaseModel):
    """
    Request for RAG query (retrieval only).
    
    Attributes:
        query: User query / research topic
        language: Output language (currently unused for retrieval)
        top_k: Number of documents to retrieve (default: 5)
    """
    query: str = Field(..., min_length=1, description="User query / research topic.")
    language: str = Field("en", description="Output language (e.g., en, de, fr).")
    top_k: Optional[int] = Field(
        5,
        ge=1,
        le=20,
        description="Number of documents to retrieve",
    )


class RAGQueryResponse(BaseModel):
    """
    Response from RAG query (retrieval only).
    
    Attributes:
        query: Original user query
        language: Language code
        answer: Generated answer (empty for retrieval-only)
        sources: List of source documents
        retrieved_chunks: Number of chunks retrieved
        message: Optional info message with document previews
        timings: Optional performance timing data
    """
    query: str
    language: str
    answer: str
    sources: Optional[List[str]] = Field(default_factory=list)
    retrieved_chunks: Optional[int] = 0
    message: Optional[str] = None
    timings: dict[str, float] = Field(
        default_factory=dict,
        description="Best-effort per-stage timings.",
    )


# ============================================================================
# Ingestion Schemas
# ============================================================================


class IngestLocalRequest(BaseModel):
    """
    Request to ingest documents from local filesystem.
    
    Attributes:
        pattern: File pattern to match (e.g., 'arxiv*' for arxiv papers only)
    """
    pattern: str = Field(
        "*",
        description="File pattern to match (e.g., 'arxiv*' for arxiv papers only)",
        examples=["*", "arxiv*", "paper_*.pdf"],
    )


class IngestArxivRequest(BaseModel):
    """
    Request to ingest papers from ArXiv.
    
    Attributes:
        query: ArXiv search query
        max_results: Maximum number of papers to fetch (1-20)
    """
    query: str = Field(
        ...,
        min_length=3,
        max_length=200,
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
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and clean query string."""
        v = v.strip()
        
        # Check for invalid queries
        if v == "=" or v == "":
            raise ValueError('Query cannot be empty or just special characters')
        
        # Check minimum length after stripping
        if len(v) < 3:
            raise ValueError('Query must be at least 3 characters long')
        
        # Check if query is just numbers or special characters
        if not any(c.isalnum() for c in v):
            raise ValueError('Query must contain at least one alphanumeric character')
        
        return v


class IngestionResponse(BaseModel):
    """
    Response from ingestion operation.
    
    Attributes:
        source: Source name (LocalFiles, ArXiv, etc.)
        documents_loaded: Number of documents fetched
        chunks_created: Number of chunks created
        chunks_ingested: Number of chunks written to Weaviate
        chunks_skipped: Number of duplicate chunks skipped
        errors: List of errors encountered (if any)
        success: Whether ingestion completed successfully
        papers: List of papers with metadata (ArXiv only)
    """
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
    papers: Optional[List[dict]] = Field(
        None,
        description="List of papers with metadata (ArXiv only)"
    )


# ============================================================================
# Admin Schemas
# ============================================================================


class RAGStatsResponse(BaseModel):
    """
    RAG index statistics.
    
    Attributes:
        collection_name: Weaviate collection name
        schema_version: Schema version string
        document_count: Number of documents in index
        exists: Whether collection exists
        error: Optional error message
    """
    collection_name: str
    schema_version: str
    document_count: int
    exists: bool
    error: Optional[str] = None


class ResetIndexResponse(BaseModel):
    """
    Response from index reset operation.
    
    Attributes:
        success: Whether reset was successful
        message: Status message
        previous_document_count: Number of documents before reset
    """
    success: bool
    message: str
    previous_document_count: Optional[int] = None