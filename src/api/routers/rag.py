"""
RAG API Router.

Endpoints for querying and managing the RAG system.
Handles document ingestion, retrieval, and index management.

Architecture Note:
    This router provides retrieval-only operations. For complete research
    workflows with multi-agent processing, use /research/query instead.
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

# Data directory configuration
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
        
    Raises:
        HTTPException: If retrieval fails
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
        
        # Format document excerpts for preview (first 3 chunks)
        excerpts = []
        for i, doc in enumerate(docs[:3], 1):
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
# Schema Endpoints
# ============================================================================


@router.post(
    "/schema/create",
    status_code=status.HTTP_200_OK,
    summary="Create Weaviate schema (collection)",
)
def create_schema():
    """
    Create the Weaviate collection schema if it doesn't exist.
    
    Useful to initialize the database before ingesting documents.
    Safe to call multiple times - won't recreate if already exists.
    
    Returns:
        Success message with schema details
    """
    try:
        with IngestionEngine() as engine:
            stats = engine.get_stats()
            
            if stats["exists"]:
                return {
                    "message": "Schema already exists",
                    "collection_name": stats["collection_name"],
                    "schema_version": stats["schema_version"],
                }
            else:
                return {
                    "message": "Schema created",
                    "collection_name": stats["collection_name"],
                    "schema_version": stats["schema_version"],
                }
    except Exception as e:
        logger.exception("Schema creation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema creation failed: {str(e)}",
        ) from e


# ============================================================================
# Ingestion Endpoints
# ============================================================================


@router.post(
    "/ingest/local",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest documents from local filesystem",
)
def ingest_local(payload: IngestLocalRequest) -> IngestionResponse:
    """
    Ingest documents from data/raw/ directory.
    
    Supports PDF and TXT files with glob pattern matching.
    Automatically skips duplicate documents based on content hash.
    
    Args:
        payload: Ingestion request with file pattern
        
    Returns:
        Ingestion statistics (documents loaded, chunks created/ingested/skipped)
        
    Raises:
        HTTPException: If ingestion fails
    """
    try:
        logger.info("Starting local ingestion with pattern: %s", payload.pattern)
        
        # Use context manager for automatic cleanup
        with IngestionEngine() as engine:
            results = []
            for data_dir in [DATA_RAW_DIR, DATA_ARXIV_DIR]:
                if not data_dir.exists():
                    logger.warning("Directory does not exist: %s", data_dir)
                    continue
                
                source = LocalFileSource(data_dir)
                result = engine.ingest_from_source(source, pattern=payload.pattern)
                results.append(result)
            
            # Aggregate results from all directories
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
                source="LocalFiles",
                documents_loaded=total_docs,
                chunks_created=total_chunks_created,
                chunks_ingested=total_chunks_ingested,
                chunks_skipped=total_chunks_skipped,
                errors=all_errors,
                success=len(all_errors) == 0,
                papers=None,
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
    summary="Download and ingest papers from ArXiv",
)
def ingest_arxiv(payload: IngestArxivRequest) -> IngestionResponse:
    """
    Download and ingest papers from ArXiv.
    
    Fetches papers matching the search query, downloads PDFs,
    extracts metadata, and ingests into the vector database.
    
    Args:
        payload: ArXiv search request with query and max_results
        
    Returns:
        Ingestion statistics with paper metadata
        
    Raises:
        HTTPException: If ingestion fails
    """
    try:
        logger.info(
            "Starting ArXiv ingestion: query='%s', max_results=%d",
            payload.query,
            payload.max_results,
        )
        
        # Use context manager for automatic cleanup
        with IngestionEngine() as engine:
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
            
            return IngestionResponse(
                source=result.source,
                documents_loaded=result.documents_loaded,
                chunks_created=result.chunks_created,
                chunks_ingested=result.chunks_ingested,
                chunks_skipped=result.chunks_skipped,
                errors=result.errors,
                success=result.success,
                papers=result.papers,
            )
        
    except Exception as e:
        logger.exception("ArXiv ingestion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ArXiv ingestion failed: {str(e)}",
        ) from e


@router.get(
    "/stats",
    response_model=RAGStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get RAG index statistics",
)
def get_stats() -> RAGStatsResponse:
    """
    Get information about the RAG vector database.
    
    Returns collection name, schema version, and document count.
    
    Returns:
        Index statistics
        
    Raises:
        HTTPException: If stats retrieval fails
    """
    # Use context manager for temporary connection
    with IngestionEngine() as engine:
        stats = engine.get_stats()
        
        return RAGStatsResponse(
            collection_name=stats["collection_name"],
            schema_version=stats["schema_version"],
            document_count=stats["document_count"],
            exists=stats["exists"],
        )


# ============================================================================
# Admin Endpoints
# ============================================================================


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
        
    Raises:
        HTTPException: If reset fails
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
    

@router.get(
    "/debug/weaviate",
    status_code=status.HTTP_200_OK,
    summary="Debug Weaviate connection and data",
)
def debug_weaviate():
    """
    Diagnostic endpoint to check Weaviate connection and collection status.
    
    Returns:
        Detailed diagnostic information about Weaviate
    """
    try:
        from ...rag.core.pipeline import RAGPipeline
        import weaviate
        
        cfg = load_config()
        
        # Parse Weaviate URL
        from urllib.parse import urlparse
        parsed = urlparse(cfg.weaviate.url if cfg.weaviate.url.startswith('http') else f'http://{cfg.weaviate.url}')
        host = parsed.hostname or 'weaviate'
        port = parsed.port or 8080
        
        # Connect to Weaviate
        client = weaviate.connect_to_local(host=host, port=port)
        
        try:
            # Check collection existence
            collection_name = "ResearchDocument"
            exists = client.collections.exists(collection_name)
            
            if not exists:
                return {
                    "status": "error",
                    "message": f"Collection '{collection_name}' does not exist",
                    "weaviate_url": f"{host}:{port}",
                    "collection_name": collection_name,
                }
            
            # Get collection stats
            collection = client.collections.get(collection_name)
            response = collection.aggregate.over_all(total_count=True)
            doc_count = response.total_count
            
            # Fetch sample document
            sample_response = collection.query.fetch_objects(limit=1)
            has_data = len(sample_response.objects) > 0
            
            sample_doc = None
            if has_data:
                obj = sample_response.objects[0]
                props = obj.properties
                sample_doc = {
                    "source": props.get('source', 'N/A'),
                    "chunk_index": props.get('chunk_index', 'N/A'),
                    "content_preview": props.get('content', '')[:200],
                }
            
            # Test RAG pipeline
            try:
                pipeline = RAGPipeline.from_existing()
                test_docs = pipeline.run(query="test", top_k=1)
                pipeline_works = len(test_docs) > 0
            except Exception as e:
                pipeline_works = False
                pipeline_error = str(e)
            
            return {
                "status": "success",
                "weaviate_url": f"{host}:{port}",
                "collection_name": collection_name,
                "collection_exists": exists,
                "document_count": doc_count,
                "has_data": has_data,
                "sample_document": sample_doc,
                "rag_pipeline_works": pipeline_works,
                "rag_pipeline_error": pipeline_error if not pipeline_works else None,
            }
            
        finally:
            client.close()
            
    except Exception as e:
        logger.exception("Weaviate diagnostic failed")
        return {
            "status": "error",
            "message": str(e),
        }