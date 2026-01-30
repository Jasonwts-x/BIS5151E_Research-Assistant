"""
RAG API Router

Endpoints for querying and managing the RAG system.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ...rag.core import RAGPipeline, RAGService
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

# ============================================================================
# Configuration - Data Directories
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_ARXIV_DIR = PROJECT_ROOT / "data" / "arxiv"

DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_ARXIV_DIR.mkdir(parents=True, exist_ok=True)

logger.info("Data directories configured: raw=%s, arxiv=%s", DATA_RAW_DIR, DATA_ARXIV_DIR)


# ============================================================================
# Query Endpoints - RETRIEVAL ONLY
# ============================================================================


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query RAG system (retrieval only - no generation)",
    description="""
    Retrieve relevant documents from the RAG vector database.
    
    **This endpoint performs document retrieval ONLY** - it does NOT run CrewAI agents or generate summaries.
    
    **For complete research workflow (RAG + multi-agent generation), use:**
    - `POST /research/query` (synchronous)
    - `POST /research/query/async` (asynchronous)
    
    **Use this endpoint when you:**
    - Only need document retrieval
    - Want to see which documents would be retrieved
    - Are building custom processing on top of RAG
    - Need to inspect retrieval quality
    
    **Returns:**
    - Query
    - Retrieved document sources
    - Number of chunks retrieved
    - Empty `answer` field (no generation performed)
    """,
)
async def rag_query(
    payload: RAGQueryRequest,
    rag: Annotated[RAGService, Depends(get_rag_service)],
) -> RAGQueryResponse:
    """
    Retrieve relevant documents from RAG system without generation.
    
    This endpoint ONLY performs retrieval - no CrewAI workflow execution.
    Use /research/query for full workflow with summary generation.
    
    Args:
        payload: Query request with search query and top_k
        rag: RAG service dependency (injected)
        
    Returns:
        Retrieved documents with sources (no answer generated)
    """
    try:
        logger.info("RAG retrieval-only query: %s", payload.query)
        
        # Retrieve documents from vector database
        pipeline = RAGPipeline.from_existing()
        docs = pipeline.run(query=payload.query, top_k=payload.top_k or 5)
        
        logger.info("Retrieved %d documents (retrieval only, no generation)", len(docs))
        
        # Extract unique sources
        sources = []
        for doc in docs:
            source = doc.meta.get("source", "unknown")
            if source not in sources:
                sources.append(source)
        
        # Format document excerpts for preview
        excerpts = []
        for i, doc in enumerate(docs[:3], 1):  # Show first 3 excerpts
            excerpt = doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            excerpts.append(f"[{i}] {excerpt}")
        
        preview_text = "\n\n".join(excerpts)
        
        return RAGQueryResponse(
            query=payload.query,
            answer="",  # No answer - retrieval only
            sources=sources,
            retrieved_chunks=len(docs),
            language=payload.language,
            message=(
                f"Retrieved {len(docs)} documents (retrieval only). "
                f"Use POST /research/query for full workflow with summary generation.\n\n"
                f"Document Previews:\n{preview_text}"
            ),
        )
        
    except Exception as e:
        logger.exception("RAG retrieval failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG retrieval failed: {str(e)}",
        ) from e


# ============================================================================
# Ingestion Endpoints
# ============================================================================


@router.post(
    "/ingest/local",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest documents from local filesystem",
    description="""
    Ingest documents from local filesystem into the RAG vector database.
    
    **Supported file types:** PDF, TXT
    
    **Source directories:**
    - `data/raw/` - Manually added documents
    - `data/arxiv/` - Downloaded ArXiv papers
    
    **Workflow:**
    1. Load matching files from both directories
    2. Extract text and chunk documents
    3. Generate embeddings
    4. Store in Weaviate vector database
    5. Deduplicate (skip already-indexed chunks)
    
    **Note:** Ingestion can take several minutes for large document sets.
    """,
)
def ingest_local(payload: IngestLocalRequest) -> IngestionResponse:
    """
    Ingest documents from local filesystem.
    
    Args:
        payload: Ingestion request with file pattern
        
    Returns:
        Ingestion statistics (documents loaded, chunks created, etc.)
    """
    try:
        logger.info("Starting local ingestion with pattern: %s", payload.pattern)
        
        engine = IngestionEngine()
        
        # Ingest from both directories
        results = []
        for data_dir in [DATA_RAW_DIR, DATA_ARXIV_DIR]:
            if not data_dir.exists():
                logger.warning("Directory does not exist: %s", data_dir)
                continue
            
            source = LocalFileSource(data_dir)
            result = engine.ingest_from_source(source, pattern=payload.pattern)
            results.append(result)
        
        # Aggregate results
        total_docs = sum(r.documents_loaded for r in results)
        total_chunks_created = sum(r.chunks_created for r in results)
        total_chunks_ingested = sum(r.chunks_ingested for r in results)
        total_chunks_skipped = sum(r.chunks_skipped for r in results)
        all_errors = [err for r in results for err in r.errors]
        
        logger.info(
            "Local ingestion complete: %d docs, %d chunks created, %d ingested, %d skipped",
            total_docs,
            total_chunks_created,
            total_chunks_ingested,
            total_chunks_skipped,
        )
        
        return IngestionResponse(
            documents_loaded=total_docs,
            chunks_created=total_chunks_created,
            chunks_ingested=total_chunks_ingested,
            chunks_skipped=total_chunks_skipped,
            errors=all_errors,
        )
        
    except Exception as e:
        logger.exception("Local ingestion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        ) from e
    
    finally:
        # Always try to close client
        try:
            if 'engine' in locals() and hasattr(engine, 'client'):
                engine.client.close()
        except Exception as e:
            logger.warning("Failed to close Weaviate client: %s", str(e))


@router.post(
    "/ingest/arxiv",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Download and ingest papers from ArXiv",
    description="""
    Download papers from ArXiv and ingest into RAG vector database.
    
    **Workflow:**
    1. Search ArXiv API for matching papers
    2. Download PDFs to `data/arxiv/`
    3. Extract text and chunk documents
    4. Generate embeddings
    5. Store in Weaviate
    
    **Query examples:**
    - "transformer neural networks"
    - "retrieval augmented generation"
    - "large language models"
    
    **Note:** Downloads can take time. Use reasonable `max_results` values (< 50).
    """,
)
def ingest_arxiv(payload: IngestArxivRequest) -> IngestionResponse:
    """
    Download and ingest papers from ArXiv.
    
    Args:
        payload: ArXiv query and max results
        
    Returns:
        Ingestion statistics
    """
    try:
        logger.info(
            "Starting ArXiv ingestion: query='%s', max_results=%d",
            payload.query,
            payload.max_results,
        )
        
        engine = IngestionEngine()
        source = ArXivSource(download_dir=DATA_ARXIV_DIR)
        
        result = engine.ingest_from_source(
            source,
            query=payload.query,
            max_results=payload.max_results,
        )
        
        logger.info(
            "ArXiv ingestion complete: %d docs, %d chunks created, %d ingested",
            result.documents_loaded,
            result.chunks_created,
            result.chunks_ingested,
        )
        
        return result
        
    except Exception as e:
        logger.exception("ArXiv ingestion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ArXiv ingestion failed: {str(e)}",
        ) from e
    
    finally:
        try:
            if 'engine' in locals() and hasattr(engine, 'client'):
                engine.client.close()
        except Exception as e:
            logger.warning("Failed to close Weaviate client: %s", str(e))


# ============================================================================
# Admin Endpoints
# ============================================================================


@router.get(
    "/stats",
    response_model=RAGStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get RAG index statistics",
)
def get_stats() -> RAGStatsResponse:
    """
    Get information about the RAG vector database.
    
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
    summary="⚠️ Clear all documents from index (DESTRUCTIVE)",
    description="""
    Clear all documents from the RAG vector database.
    
    **⚠️ WARNING: This deletes ALL indexed documents!**
    
    **Use cases:**
    - Reset after schema changes
    - Clean up test data
    - Start fresh with new documents
    
    **After reset, you must re-ingest documents:**
    - POST /rag/ingest/local
    - POST /rag/ingest/arxiv
    """,
)
def reset_index() -> ResetIndexResponse:
    """
    Clear all documents from the RAG index.
    
    **⚠️ WARNING: This is destructive and cannot be undone!**
    
    Returns:
        Success status and number of documents deleted
    """
    try:
        logger.warning("Reset index requested - all documents will be deleted!")
        
        # Get current count before deletion
        engine = IngestionEngine()
        stats = engine.get_stats()
        previous_count = stats.get("document_count", 0)
        
        # Clear the index
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