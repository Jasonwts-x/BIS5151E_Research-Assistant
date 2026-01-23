"""
RAG API Router

Endpoints for querying and managing the RAG system.
"""
from __future__ import annotations

import logging
import os
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from ...rag.core import RAGService
from ...rag.ingestion import IngestionEngine
from ...rag.sources import ArXivSource, LocalFileSource
from ...utils.config import load_config
from ..dependencies import get_rag_service
from ..errors import internal_server_error
from ..openapi import APITag
from ..schemas.rag import (
    IngestArxivRequest,
    IngestLocalRequest,
    IngestionResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGStatsResponse,
    ResetIndexResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=[APITag.RAG])

# CrewAI service URL (internal Docker network)
CREWAI_URL = os.getenv("CREWAI_URL", "http://crewai:8100")

# Get data directory from config
def get_data_dir():
    """Get data directory from config or environment."""
    from pathlib import Path
    data_dir_str = os.getenv("DATA_DIR")
    if data_dir_str:
        return Path(data_dir_str)
    # Fallback to default
    return Path("/workspaces/BIS5151E_Research-Assistant/data/raw")

DATA_DIR = get_data_dir()


# ============================================================================
# Query Endpoints
# ============================================================================


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Run RAG + generation and return a final answer.",
)
async def rag_query(
    payload: RAGQueryRequest,
    rag: Annotated[RAGService, Depends(get_rag_service)],
) -> RAGQueryResponse:
    """
    Execute full RAG pipeline with multi-agent processing.
    
    This endpoint:
    1. Retrieves relevant context using RAG (Weaviate + hybrid search)
    2. Forwards the query to the CrewAI service for agent processing
    3. Returns the final fact-checked summary
    
    The CrewAI service handles:
    - Writer agent: Drafts initial summary
    - Reviewer agent: Improves clarity and coherence
    - FactChecker agent: Verifies claims and citations
    - (Future: Translator agent for non-English output)
    
    Note: This is the recommended user-facing endpoint for research queries.
    For more control, you can call /crewai/run directly and manage RAG retrieval yourself.
    """
    try:
        logger.info(
            "RAG query request: topic='%s', language='%s'",
            payload.query,
            payload.language,
        )
        
        # Forward to CrewAI service (which handles RAG retrieval internally)
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{CREWAI_URL}/crew/run",
                json={
                    "topic": payload.query,
                    "language": payload.language,
                },
            )
            response.raise_for_status()
            
            crew_result = response.json()
            
            logger.info("CrewAI service completed successfully")
            
            return RAGQueryResponse(
                query=payload.query,
                language=payload.language,
                answer=crew_result["answer"],
                timings={},
            )
            
    except httpx.HTTPStatusError as e:
        logger.error("CrewAI service returned error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"CrewAI service error: {e.response.text}",
        ) from e
        
    except httpx.RequestError as e:
        logger.error("Failed to reach CrewAI service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e
        
    except Exception as err:
        logger.exception("RAG query failed internally.")
        raise internal_server_error(
            "An error occurred while processing the request."
        ) from err


# ============================================================================
# Ingestion Endpoints
# ============================================================================


@router.post(
    "/ingest/local",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest documents from local filesystem (data/raw/).",
)
def ingest_local(payload: IngestLocalRequest) -> IngestionResponse:
    """
    Ingest documents from local filesystem.
    
    Files are loaded from `data/raw/` directory.
    Supports: PDF, TXT files
    
    Workflow:
    1. Load matching files from data/raw/
    2. Chunk documents
    3. Generate embeddings
    4. Write to Weaviate (skip duplicates)
    
    Note: This is idempotent - re-ingesting same files will skip duplicates.
    """
    try:
        logger.info("Ingesting local files with pattern: %s", payload.pattern)
        
        # Create ingestion engine
        engine = IngestionEngine()
        
        # Ingest from local source
        source = LocalFileSource(DATA_DIR)
        result = engine.ingest_from_source(source, pattern=payload.pattern)
        
        logger.info(
            "Local ingestion complete: %d docs, %d chunks ingested",
            result.documents_loaded,
            result.chunks_ingested,
        )
        
        return IngestionResponse(
            source=result.source_name,
            documents_loaded=result.documents_loaded,
            chunks_created=result.chunks_created,
            chunks_ingested=result.chunks_ingested,
            chunks_skipped=result.chunks_skipped,
            errors=result.errors,
            success=len(result.errors) == 0,
        )
        
    except Exception as e:
        logger.exception("Local ingestion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        ) from e


@router.post(
    "/ingest/arxiv",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch and ingest papers from ArXiv.",
)
def ingest_arxiv(payload: IngestArxivRequest) -> IngestionResponse:
    """
    Fetch papers from ArXiv and ingest into RAG system.
    
    Workflow:
    1. Search ArXiv for relevant papers
    2. Filter by relevance score
    3. Download PDFs to data/raw/
    4. Extract metadata (authors, date, category, abstract)
    5. Chunk and embed papers
    6. Write to Weaviate (skip duplicates)
    
    Features:
    - Automatic relevance filtering
    - Metadata enrichment
    - Abstract extraction for better retrieval
    - Idempotent (re-fetching same papers skips duplicates)
    
    Note: This may take 30-90 seconds for max_results=5 (downloading PDFs).
    """
    engine = None
    try:
        logger.info(
            "Ingesting from ArXiv: query='%s', max_results=%d",
            payload.query,
            payload.max_results,
        )
        
        # Create ingestion engine
        engine = IngestionEngine()
        
        # Ingest from ArXiv source with relevance filtering
        source = ArXivSource(
            download_dir=DATA_DIR,
            min_relevance_score=0.3  # Configurable threshold
        )
        result = engine.ingest_from_source(
            source,
            query=payload.query,
            max_results=payload.max_results,
        )
        
        logger.info(
            "ArXiv ingestion complete: %d papers, %d chunks ingested",
            result.documents_loaded,
            result.chunks_ingested,
        )
        
        # Check if any papers were found
        if result.documents_loaded == 0:
            logger.warning("No relevant papers found for query: %s", payload.query)
            return IngestionResponse(
                source=result.source_name,
                documents_loaded=0,
                chunks_created=0,
                chunks_ingested=0,
                chunks_skipped=0,
                errors=result.errors or ["No relevant papers found for this query"],
                success=False,
                papers=[]
            )
        
        # Check if ingestion succeeded
        if result.errors:
            logger.error("Ingestion encountered errors: %s", result.errors)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ingestion failed: {'; '.join(result.errors)}",
            )

        return IngestionResponse(
            source=result.source_name,
            documents_loaded=result.documents_loaded,
            chunks_created=result.chunks_created,
            chunks_ingested=result.chunks_ingested,
            chunks_skipped=result.chunks_skipped,
            errors=result.errors,
            success=len(result.errors) == 0 and result.chunks_ingested > 0,
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # Validation error
        logger.error("Invalid query: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("ArXiv ingestion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ArXiv ingestion failed: {str(e)}",
        ) from e
    finally:
        # Properly close the Weaviate client
        if engine is not None and hasattr(engine, 'client'):
            try:
                engine.client.close()
                logger.debug("Weaviate client closed successfully.")
            except Exception as e:
                logger.warning("Failed to close Weaviate client: %s", str(e))


# ============================================================================
# Admin Endpoints
# ============================================================================


@router.get(
    "/stats",
    response_model=RAGStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get RAG index statistics.",
)
def get_stats() -> RAGStatsResponse:
    """
    Get information about the RAG index.
    
    Returns:
    - Collection name
    - Schema version
    - Number of indexed chunks
    - Whether index exists
    """
    try:
        engine = IngestionEngine()
        stats = engine.get_stats()
        
        return RAGStatsResponse(**stats)
        
    except Exception as e:
        logger.exception("Failed to get stats")
        return RAGStatsResponse(
            collection_name="unknown",
            schema_version="unknown",
            document_count=0,
            exists=False,
            error=str(e),
        )


@router.delete(
    "/admin/reset-index",
    response_model=ResetIndexResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear all documents from index (WARNING: DESTRUCTIVE).",
)
def reset_index() -> ResetIndexResponse:
    """
    Clear all documents from the RAG index.
    
    ⚠️  WARNING: This deletes ALL indexed documents!
    
    Use cases:
    - Reset after schema changes
    - Clean up test data
    - Start fresh with new documents
    
    After reset, you must re-ingest documents:
    - POST /rag/ingest/local
    - POST /rag/ingest/arxiv
    """
    try:
        logger.warning("Reset index requested - all documents will be deleted!")
        
        # Get current count
        engine = IngestionEngine()
        stats = engine.get_stats()
        previous_count = stats.get("document_count", 0)
        
        # Clear index
        engine.clear_index()
        
        logger.info("Index reset complete - %d documents deleted", previous_count)
        
        return ResetIndexResponse(
            success=True,
            message=f"Index cleared successfully. {previous_count} documents deleted.",
            previous_document_count=previous_count,
        )
        
    except Exception as e:
        logger.exception("Failed to reset index")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset index: {str(e)}",
        ) from e


# ============================================================================
# Future Endpoints (Placeholders)
# ============================================================================
# TODO (Step F): Add /rag/retrieve endpoint (retrieval without generation)
# TODO (Step G): Add /rag/export endpoint (export index to file)
# TODO (Step G): Add /rag/import endpoint (import index from file)