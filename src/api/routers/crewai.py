"""
CrewAI Router - API Gateway Proxy.

Proxies requests from the API gateway to the CrewAI service.
Provides endpoints for synchronous and asynchronous multi-agent workflows.
"""
from __future__ import annotations

import logging
import os

import httpx
from fastapi import APIRouter, HTTPException, status

from ..openapi import APITag
from ..schemas.crewai import (
    CrewAsyncRunResponse,
    CrewRunRequest,
    CrewRunResponse,
    CrewStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crewai", tags=[APITag.CREWAI])

# Get CrewAI service URL from environment
CREWAI_URL = os.getenv("CREWAI_URL", "http://crewai:8100")

logger.info("CrewAI router configured: crewai_url=%s", CREWAI_URL)


# ============================================================================
# Health Endpoints
# ============================================================================


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Check CrewAI service health",
)
async def health():
    """
    Proxy health check to CrewAI service.
    
    Useful for monitoring and debugging connectivity between gateway and crew service.
    
    Returns:
        Health status from CrewAI service
        
    Raises:
        HTTPException: If CrewAI service is unreachable
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{CREWAI_URL}/health")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error("CrewAI service unreachable: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e
    except httpx.HTTPStatusError as e:
        logger.error("CrewAI service returned error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e


# ============================================================================
# Execution Endpoints
# ============================================================================


@router.post(
    "/run",
    response_model=CrewRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute research query (synchronous)",
)
async def crewai_run(payload: CrewRunRequest) -> CrewRunResponse:
    """
    Execute research query using CrewAI multi-agent workflow.
    
    **This is a synchronous endpoint that blocks until completion (30-60s).**
    
    For async execution, use POST /crewai/run/async instead.
    
    Args:
        payload: Research query request with topic and language
        
    Returns:
        Research summary with evaluation metrics
        
    Raises:
        HTTPException: If CrewAI execution fails
    """
    try:
        logger.info("Forwarding synchronous crew run: topic='%s'", payload.topic)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{CREWAI_URL}/run",
                json=payload.model_dump(),
            )
            response.raise_for_status()

            return CrewRunResponse(**response.json())

    except httpx.HTTPStatusError as e:
        logger.error("CrewAI returned error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e
    except httpx.RequestError as e:
        logger.error("Failed to reach CrewAI service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e


@router.post(
    "/run/async",
    response_model=CrewAsyncRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute research query (asynchronous)",
)
async def crewai_run_async(payload: CrewRunRequest) -> CrewAsyncRunResponse:
    """
    Execute research query asynchronously.
    
    Returns immediately with a job_id. Use GET /status/{job_id} to check progress.
    
    Args:
        payload: Research query request
        
    Returns:
        Job information with job_id for status tracking
        
    Raises:
        HTTPException: If job submission fails
    """
    try:
        logger.info("Forwarding async crew run: topic='%s'", payload.topic)

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{CREWAI_URL}/run/async",
                json=payload.model_dump(),
            )
            response.raise_for_status()

            return CrewAsyncRunResponse(**response.json())

    except httpx.HTTPStatusError as e:
        logger.error("CrewAI returned error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e
    except httpx.RequestError as e:
        logger.error("Failed to reach CrewAI service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e


@router.get(
    "/status/{job_id}",
    response_model=CrewStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get async job status",
)
async def get_status(job_id: str) -> CrewStatusResponse:
    """
    Get status of an async CrewAI job.
    
    Args:
        job_id: Job identifier from async submission
        
    Returns:
        Job status (pending/running/completed/failed) with results if complete
        
    Raises:
        HTTPException: If job not found or service unreachable
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{CREWAI_URL}/status/{job_id}")
            response.raise_for_status()

            return CrewStatusResponse(**response.json())

    except httpx.HTTPStatusError as e:
        logger.error("CrewAI returned error for job %s: %s", job_id, e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e
    except httpx.RequestError as e:
        logger.error("Failed to reach CrewAI service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e