"""
Research API Router

Primary user-facing endpoints for research queries.
Orchestrates the complete RAG + CrewAI + Evaluation workflow.
"""
from __future__ import annotations

import logging
import os
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from ...rag.core import RAGPipeline, RAGService
from ..dependencies import get_rag_service
from ..openapi import APITag
from ..schemas.research import (
    ResearchAsyncResponse,
    ResearchQueryRequest,
    ResearchQueryResponse,
    ResearchStatusResponse,
)
from ..schemas.crewai import CrewRunRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=[APITag.RESEARCH])

# Get service URLs from environment
CREWAI_URL = os.getenv("CREWAI_URL", "http://crewai:8100")
EVAL_URL = os.getenv("EVAL_URL", "http://eval:8502")

logger.info("Research router initialized: crewai_url=%s, eval_url=%s", CREWAI_URL, EVAL_URL)


# ============================================================================
# Synchronous Research Query
# ============================================================================


@router.post(
    "/query",
    response_model=ResearchQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute research query (synchronous)",
    description="""
    Execute a complete research workflow with RAG retrieval and multi-agent processing.
    
    **This is the PRIMARY endpoint for research queries.**
    
    ## Workflow
    
    1. **RAG Retrieval**: Search vector database for relevant academic papers
    2. **Multi-Agent Processing**:
       - Writer agent drafts initial summary from retrieved context
       - Reviewer agent improves clarity and coherence
       - FactChecker agent verifies all claims against sources
       - Translator agent translates to target language (if requested)
    3. **Evaluation**: Generate quality metrics (TruLens + Guardrails)
    4. **Return**: Fact-checked summary with proper citations and metrics
    
    ## Performance
    
    - Typical execution time: **30-60 seconds**
    - This endpoint **blocks** until completion
    - For async execution, use `POST /research/query/async`
    """,
)
async def research_query(
    request: ResearchQueryRequest,
    rag: Annotated[RAGService, Depends(get_rag_service)],
) -> ResearchQueryResponse:
    """
    Execute complete research workflow (synchronous).
    
    Args:
        request: Research query request with query, language, and options
        rag: RAG service dependency (injected)
        
    Returns:
        Research summary with citations, sources, and evaluation metrics
        
    Raises:
        HTTPException: If RAG retrieval, crew execution, or evaluation fails
    """
    try:
        logger.info("Research query initiated: query='%s', language='%s'", request.query, request.language)
        
        # Step 1: RAG Retrieval
        logger.info("Step 1/4: Retrieving relevant documents from RAG...")
        
        pipeline = RAGPipeline.from_existing()
        docs = pipeline.run(query=request.query, top_k=request.top_k or 5)
        
        logger.info("Retrieved %d documents from RAG", len(docs))
        
        if not docs:
            logger.warning("No documents retrieved for query: %s", request.query)
        
        # Extract sources and context for response
        sources = []
        context_chunks = []
        for doc in docs:
            source = doc.meta.get("source", "unknown")
            if source not in sources:
                sources.append(source)
            context_chunks.append(doc.content)
        
        # Combine context for evaluation
        combined_context = "\n\n".join(context_chunks)
        
        # Step 2: CrewAI Execution
        logger.info("Step 2/4: Executing multi-agent workflow...")
        
        crew_request = CrewRunRequest(
            topic=request.query,
            language=request.language,
        )
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{CREWAI_URL}/run",
                json=crew_request.model_dump(),
            )
            response.raise_for_status()
            crew_result = response.json()
        
        summary = crew_result.get("summary", "")
        metadata = crew_result.get("metadata", {})
        
        logger.info("Multi-agent workflow completed, summary length: %d chars", len(summary))
        
        # Step 3: Evaluation (if enabled)
        evaluation = None
        if request.enable_evaluation:
            logger.info("Step 3/4: Running evaluation...")
            
            try:
                eval_request = {
                    "query": request.query,
                    "answer": summary,
                    "context": combined_context,
                    "language": request.language,
                    "metadata": {
                        "sources_count": len(sources),
                        "chunks_retrieved": len(docs),
                        **metadata,
                    },
                }
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    eval_response = await client.post(
                        f"{EVAL_URL}/metrics/evaluate",
                        json=eval_request,
                    )
                    eval_response.raise_for_status()
                    evaluation = eval_response.json()
                
                logger.info("Evaluation completed: record_id=%s, overall_score=%.2f",
                           evaluation.get("record_id"),
                           evaluation.get("summary", {}).get("overall_score", 0))
                
            except Exception as e:
                logger.error("Evaluation failed (non-fatal): %s", e)
                evaluation = {"error": str(e), "status": "failed"}
        else:
            logger.info("Step 3/4: Evaluation skipped (disabled)")
        
        # Step 4: Build response
        logger.info("Step 4/4: Building response...")
        
        return ResearchQueryResponse(
            query=request.query,
            summary=summary,
            language=request.language,
            sources=sources,
            retrieved_chunks=len(docs),
            evaluation=evaluation,
            metadata={
                "crew_metadata": metadata,
                "evaluation_enabled": request.enable_evaluation,
            },
        )
        
    except httpx.HTTPStatusError as e:
        logger.error("Service returned error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Service error: {e.response.text}",
        ) from e
        
    except httpx.RequestError as e:
        logger.error("Failed to reach service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        ) from e
        
    except Exception as e:
        logger.exception("Research query failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research query failed: {str(e)}",
        ) from e


# ============================================================================
# Asynchronous Research Query
# ============================================================================


@router.post(
    "/query/async",
    response_model=ResearchAsyncResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute research query (asynchronous)",
    description="""
    Execute a complete research workflow asynchronously.
    
    **Use this endpoint for:**
    - Long-running queries
    - Batch processing
    - Non-blocking execution
    
    ## Workflow
    
    1. **Immediate Response**: Returns `job_id` immediately
    2. **Background Processing**: Query executes in background (30-60s)
    3. **Status Polling**: Check status with `GET /research/status/{job_id}`
    4. **Result Retrieval**: Get final result when status is 'completed'
    """,
)
async def research_query_async(
    request: ResearchQueryRequest,
    rag: Annotated[RAGService, Depends(get_rag_service)],
) -> ResearchAsyncResponse:
    """
    Execute complete research workflow (asynchronous).
    
    Args:
        request: Research query request
        rag: RAG service dependency (injected)
        
    Returns:
        Job information with job_id for status tracking
        
    Raises:
        HTTPException: If job submission fails
    """
    try:
        logger.info("Async research query initiated: query='%s'", request.query)
        
        # Step 1: RAG Retrieval (synchronous - fast operation)
        logger.info("Retrieving documents from RAG for async query...")
        
        pipeline = RAGPipeline.from_existing()
        docs = pipeline.run(query=request.query, top_k=request.top_k or 5)
        
        logger.info("Retrieved %d documents for async processing", len(docs))
        
        # Step 2: Submit to async crew execution
        logger.info("Submitting to CrewAI async execution...")
        
        crew_request = CrewRunRequest(
            topic=request.query,
            language=request.language,
        )
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{CREWAI_URL}/run/async",
                json=crew_request.model_dump(),
            )
            response.raise_for_status()
            async_result = response.json()
        
        job_id = async_result["job_id"]
        logger.info("Async job created: job_id=%s, documents=%d", job_id, len(docs))
        
        return ResearchAsyncResponse(
            job_id=job_id,
            status="pending",
            message=f"Research job submitted successfully. Retrieved {len(docs)} documents from RAG.",
            query=request.query,
        )
        
    except Exception as e:
        logger.exception("Failed to submit async research query")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit async job: {str(e)}",
        ) from e


@router.get(
    "/status/{job_id}",
    response_model=ResearchStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get async job status",
)
async def get_status(job_id: str) -> ResearchStatusResponse:
    """
    Get status of an async research job.
    
    Args:
        job_id: Job identifier from async request
        
    Returns:
        Job status and result (if completed)
        
    Raises:
        HTTPException: If job not found or service unavailable
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{CREWAI_URL}/status/{job_id}")
            response.raise_for_status()
            
            return ResearchStatusResponse(**response.json())
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}",
            ) from e
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e