"""
Research API Router

Primary user-facing endpoints for research queries.
Orchestrates the complete RAG + CrewAI workflow.

This router provides the main value proposition of the system:
1. Retrieve relevant academic papers from vector database
2. Execute multi-agent workflow to generate fact-checked summaries
3. Return high-quality research summaries with proper citations

Workflow:
    User Query
        ↓
    RAG Retrieval (Weaviate)
        ↓
    CrewAI Multi-Agent Processing
        ├── Writer: Draft initial summary
        ├── Reviewer: Improve clarity
        ├── FactChecker: Verify claims
        └── Translator: Translate (if requested)
        ↓
    Evaluation (TruLens + Guardrails)
        ↓
    Final Research Summary
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

# Get CrewAI service URL from environment
CREWAI_URL = os.getenv("CREWAI_URL", "http://crewai:8100")

logger.info("Research router initialized: crewai_url=%s", CREWAI_URL)


# ============================================================================
# Synchronous Research Query
# ============================================================================


@router.post(
    "/query",
    response_model=ResearchQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="⭐ Execute research query (synchronous)",
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
    3. **Evaluation**: Generate quality metrics (optional)
    4. **Return**: Fact-checked summary with proper citations
    
    ## Performance
    
    - Typical execution time: **30-60 seconds**
    - This endpoint **blocks** until completion
    - For async execution, use `POST /research/query/async`
    
    ## Example Request
```json
    {
      "query": "What is retrieval augmented generation?",
      "language": "en",
      "top_k": 5,
      "enable_evaluation": true
    }
```
    
    ## Example Response
```json
    {
      "query": "What is retrieval augmented generation?",
      "summary": "Retrieval Augmented Generation (RAG) is...[1][2]\\n\\n## References\\n[1] Source 1\\n[2] Source 2",
      "language": "en",
      "sources": ["paper1.pdf", "paper2.pdf"],
      "retrieved_chunks": 5,
      "evaluation": {
        "performance": {"total_time": 45.2},
        "trulens": {"overall_score": 0.85},
        "guardrails": {"input_passed": true, "output_passed": true}
      }
    }
```
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
        HTTPException: If RAG retrieval or crew execution fails
    """
    try:
        logger.info("Research query initiated: query='%s', language='%s'", request.query, request.language)
        
        # Step 1: RAG Retrieval
        logger.info("Step 1/3: Retrieving relevant documents from RAG...")
        
        pipeline = RAGPipeline.from_existing()
        docs = pipeline.run(query=request.query, top_k=request.top_k or 5)
        
        logger.info("Retrieved %d documents from RAG", len(docs))
        
        if not docs:
            logger.warning("No documents retrieved for query: %s", request.query)
        
        # Extract sources for response
        sources = []
        for doc in docs:
            source = doc.meta.get("source", "unknown")
            if source not in sources:
                sources.append(source)
        
        # Step 2: CrewAI Execution
        logger.info("Step 2/3: Executing multi-agent workflow...")
        
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
        
        logger.info("Multi-agent workflow completed successfully")
        
        # Step 3: Format Response
        logger.info("Step 3/3: Formatting response...")
        
        evaluation = crew_result.get("evaluation") if request.enable_evaluation else None
        
        return ResearchQueryResponse(
            query=request.query,
            summary=crew_result["answer"],
            language=request.language,
            sources=sources,
            retrieved_chunks=len(docs),
            evaluation=evaluation,
            metadata={
                "crew_execution_time": evaluation.get("performance", {}).get("total_time") if evaluation else None,
                "documents_retrieved": len(docs),
                "unique_sources": len(sources),
            },
        )
        
    except httpx.HTTPStatusError as e:
        logger.error("CrewAI service error: %s - %s", e.response.status_code, e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"CrewAI service error: {e.response.text}",
        ) from e
        
    except httpx.RequestError as e:
        logger.error("CrewAI service unreachable: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e
        
    except Exception as e:
        logger.exception("Research query failed with unexpected error")
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
    summary="⭐ Execute research query (asynchronous)",
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
    
    ## Usage Pattern
```python
    # Step 1: Submit query
    response = requests.post("/research/query/async", json={
        "query": "What is machine learning?",
        "language": "en"
    })
    job_id = response.json()["job_id"]
    
    # Step 2: Poll status
    while True:
        status = requests.get(f"/research/status/{job_id}").json()
        if status["status"] == "completed":
            result = status["result"]
            break
        elif status["status"] == "failed":
            error = status["error"]
            break
        time.sleep(5)  # Poll every 5 seconds
```
    
    ## Example Request
```json
    {
      "query": "Explain neural networks",
      "language": "en",
      "top_k": 5
    }
```
    
    ## Example Response
```json
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "pending",
      "message": "Research job submitted successfully. Retrieved 5 documents.",
      "estimated_time": 45
    }
```
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
        
        async with httpx.AsyncClient(timeout=10.0) as client:
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
            estimated_time=45,  # Typical execution time
        )
        
    except httpx.HTTPStatusError as e:
        logger.error("CrewAI async submission error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Async submission failed: {e.response.text}",
        ) from e
        
    except httpx.RequestError as e:
        logger.error("CrewAI service unreachable: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e
        
    except Exception as e:
        logger.exception("Async research query submission failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Async submission failed: {str(e)}",
        ) from e


# ============================================================================
# Job Status Endpoint
# ============================================================================


@router.get(
    "/status/{job_id}",
    response_model=ResearchStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get research job status",
    description="""
    Check the status of an asynchronous research query.
    
    **Use after calling** `POST /research/query/async`
    
    ## Job Status Values
    
    - `pending`: Job is queued, waiting to start
    - `running`: Job is currently executing
    - `completed`: Job finished successfully ✅
      - Result available in `result` field
    - `failed`: Job encountered an error ❌
      - Error message available in `error` field
    
    ## Polling Recommendations
    
    - Poll interval: **5 seconds**
    - Timeout: **120 seconds** (typical job takes 30-60s)
    - Stop polling when status is `completed` or `failed`
    
    ## Example Response (Completed)
```json
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "progress": 1.0,
      "created_at": "2025-01-30T10:00:00Z",
      "started_at": "2025-01-30T10:00:05Z",
      "completed_at": "2025-01-30T10:00:50Z",
      "result": {
        "query": "What is machine learning?",
        "summary": "Machine learning is...[1][2]",
        "sources": ["paper1.pdf", "paper2.pdf"],
        "retrieved_chunks": 5
      }
    }
```
    """,
)
async def get_research_status(job_id: str) -> ResearchStatusResponse:
    """
    Get status and results of an async research job.
    
    Args:
        job_id: Unique job identifier from async submission
        
    Returns:
        Job status with result (if completed) or error (if failed)
        
    Raises:
        HTTPException: If job not found or service unavailable
    """
    try:
        logger.debug("Fetching status for job: %s", job_id)
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{CREWAI_URL}/status/{job_id}")
            response.raise_for_status()
            crew_status = response.json()
        
        logger.debug("Job %s status: %s", job_id, crew_status["status"])
        
        # Map crew status to research status
        result = None
        if crew_status["status"] == "completed" and "result" in crew_status:
            crew_result = crew_status["result"]
            result = ResearchQueryResponse(
                query=crew_result.get("topic", ""),
                summary=crew_result.get("answer", ""),
                language=crew_result.get("language", "en"),
                sources=crew_result.get("sources", []),
                retrieved_chunks=crew_result.get("retrieved_chunks", 0),
                evaluation=crew_result.get("evaluation"),
            )
        
        return ResearchStatusResponse(
            job_id=job_id,
            status=crew_status["status"],
            progress=crew_status.get("progress", 0.0),
            created_at=crew_status.get("created_at", ""),
            started_at=crew_status.get("started_at"),
            completed_at=crew_status.get("completed_at"),
            result=result,
            error=crew_status.get("error"),
        )
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning("Job not found: %s", job_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found. It may have expired or never existed.",
            ) from e
        
        logger.error("CrewAI service error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e
        
    except httpx.RequestError as e:
        logger.error("CrewAI service unreachable: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e