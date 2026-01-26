"""
CrewAI Router - API Gateway Proxy

Proxies requests to the CrewAI service.
"""
from __future__ import annotations

import logging
import os

import httpx
from fastapi import APIRouter, HTTPException, status

from ..schemas.crewai import (
    CrewAsyncRunResponse,
    CrewRunRequest,
    CrewRunResponse,
    CrewStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["crewai"])

# Get CrewAI service URL from environment
CREWAI_URL = os.getenv("CREWAI_URL", "http://crewai:8100")


@router.post(
    "/query",
    response_model=CrewRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Query research assistant (synchronous)",
)
async def crewai_run(payload: CrewRunRequest) -> CrewRunResponse:
    """
    Execute research query using CrewAI multi-agent workflow.
    
    **This is a synchronous endpoint that blocks until completion (30-60s).**
    
    For async execution, use POST /rag/query/async instead.
    
    The workflow:
    1. Retrieves relevant context from vector database
    2. Runs multi-agent pipeline (Writer → Reviewer → FactChecker)
    3. Evaluates output quality (TruLens + Guardrails)
    4. Returns fact-checked summary with evaluation metrics
    
    Example:
        POST /rag/query
        {
            "topic": "What are the benefits of retrieval-augmented generation?",
            "language": "en"
        }
    """
    try:
        logger.info(
            "Proxying crew run request to %s: topic='%s'",
            CREWAI_URL,
            payload.topic,
        )
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{CREWAI_URL}/run",
                json=payload.model_dump(),
            )
            response.raise_for_status()
            
            result = CrewRunResponse(**response.json())
            
            logger.info("Crew run completed successfully")
            return result
            
    except httpx.HTTPStatusError as e:
        logger.error("CrewAI service returned error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"CrewAI service error: {e.response.text}",
        ) from e
    except httpx.RequestError as e:
        logger.error("Failed to connect to CrewAI service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error in crew run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        ) from e


@router.post(
    "/query/async",
    response_model=CrewAsyncRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Query research assistant (asynchronous)",
)
async def crewai_run_async(payload: CrewRunRequest) -> CrewAsyncRunResponse:
    """
    Execute research query asynchronously.
    
    **This endpoint returns immediately with a job_id.**
    
    Use GET /rag/query/status/{job_id} to check progress.
    
    Example:
        POST /rag/query/async
        {
            "topic": "Explain transformer architecture",
            "language": "en"
        }
        
        Response:
        {
            "job_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "pending",
            "message": "Job created..."
        }
    """
    try:
        logger.info(
            "Proxying async crew run request to %s: topic='%s'",
            CREWAI_URL,
            payload.topic,
        )
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CREWAI_URL}/run/async",
                json=payload.model_dump(),
            )
            response.raise_for_status()
            
            result = CrewAsyncRunResponse(**response.json())
            
            logger.info("Async crew job created: %s", result.job_id)
            return result
            
    except httpx.HTTPStatusError as e:
        logger.error("CrewAI service returned error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"CrewAI service error: {e.response.text}",
        ) from e
    except httpx.RequestError as e:
        logger.error("Failed to connect to CrewAI service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e


@router.get(
    "/query/status/{job_id}",
    response_model=CrewStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get async job status",
)
async def get_query_status(job_id: str) -> CrewStatusResponse:
    """
    Get the status of an async research query job.
    
    Poll this endpoint to check if your job is complete.
    
    Status values:
    - **pending**: Job queued
    - **running**: Job executing
    - **completed**: Job done (result available)
    - **failed**: Job failed (error available)
    """
    try:
        logger.info("Proxying status check to %s for job: %s", CREWAI_URL, job_id)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{CREWAI_URL}/status/{job_id}")
            response.raise_for_status()
            
            result = CrewStatusResponse(**response.json())
            
            return result
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}",
            ) from e
        logger.error("CrewAI service returned error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"CrewAI service error: {e.response.text}",
        ) from e
    except httpx.RequestError as e:
        logger.error("Failed to connect to CrewAI service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e