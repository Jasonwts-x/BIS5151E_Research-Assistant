"""
CrewAI Router - API Gateway Proxy

Proxies requests to the CrewAI service.
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
    """
    try:
        logger.info("Proxying CrewAI run request: topic=%s", payload.topic)
        
        async with httpx.AsyncClient(timeout=1500.0) as client:
            response = await client.post(
                f"{CREWAI_URL}/run",
                json=payload.model_dump(),
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("CrewAI run completed successfully")
            
            return CrewRunResponse(**result)
            
    except httpx.HTTPStatusError as e:
        logger.error("CrewAI service error: %s", e.response.text)
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


@router.post(
    "/run/async",
    response_model=CrewAsyncRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute research query (asynchronous)",
)
async def crewai_run_async(payload: CrewRunRequest) -> CrewAsyncRunResponse:
    """Execute research query asynchronously - returns job_id immediately."""
    try:
        logger.info("Proxying async CrewAI request: topic=%s", payload.topic)
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{CREWAI_URL}/run/async",
                json=payload.model_dump(),
            )
            response.raise_for_status()
            return CrewAsyncRunResponse(**response.json())
            
    except httpx.HTTPStatusError as e:
        logger.error("CrewAI service error: %s", e.response.text)
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
async def crewai_status(job_id: str) -> CrewStatusResponse:
    """Get status of asynchronous job."""
    try:
        logger.info("Checking status for job: %s", job_id)
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{CREWAI_URL}/status/{job_id}")
            response.raise_for_status()
            return CrewStatusResponse(**response.json())
            
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
        logger.error("Failed to reach CrewAI service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e