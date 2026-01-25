from __future__ import annotations

import logging
import os
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Path, status

from ..openapi import APITag
from ..schemas.crewai import (
    CrewAsyncRunResponse,
    CrewRunRequest,
    CrewRunResponse,
    CrewStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crewai", tags=[APITag.CREWAI])

CREWAI_URL = os.getenv("CREWAI_URL", "http://crewai:8100")


@router.post(
    "/run",
    response_model=CrewRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute CrewAI workflow synchronously (BLOCKS until complete)",
)
async def crewai_run(payload: CrewRunRequest) -> CrewRunResponse:
    """
    Execute the CrewAI research workflow via the crewai service.
    
    **WARNING: This endpoint blocks for 30-60 seconds while crew executes.**
    
    For non-blocking execution, use POST /crewai/run/async instead.
    
    This endpoint acts as a gateway/proxy to the internal crewai service.
    
    Workflow:
    1. Retrieve relevant context from RAG pipeline
    2. Writer agent drafts initial summary
    3. Reviewer agent improves clarity and coherence
    4. FactChecker agent verifies all claims and citations
    5. (Future: Translator agent for non-English output)
    
    The crewai service runs independently and can be scaled separately.
    """
    try:
        logger.info(
            "Proxying crewai run request to %s/run: topic='%s', language='%s'",
            CREWAI_URL,
            payload.topic,
            payload.language,
        )
        
        # Forward request to crewai service
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{CREWAI_URL}/run",
                json=payload.model_dump(),
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info("CrewAI service returned successfully")
            
            return CrewRunResponse(**data)
            
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
        
    except Exception as e:
        logger.exception("Unexpected error in crewai proxy")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        ) from e


@router.post(
    "/run/async",
    response_model=CrewAsyncRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute CrewAI workflow asynchronously (returns immediately)",
)
async def crewai_run_async(payload: CrewRunRequest) -> CrewAsyncRunResponse:
    """
    Execute the CrewAI research workflow asynchronously.
    
    **This endpoint returns immediately with a job_id.**
    
    Use GET /crewai/status/{job_id} to check progress and retrieve results.
    
    Ideal for:
    - Web UIs (can show progress indicators)
    - N8N workflows (wait/poll pattern)
    - Batch processing (submit many jobs, collect later)
    """
    try:
        logger.info(
            "Proxying async crewai run to %s/run/async: topic='%s', language='%s'",
            CREWAI_URL,
            payload.topic,
            payload.language,
        )
        
        # Forward request to crewai service
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{CREWAI_URL}/run/async",  # Internal service has no prefix
                json=payload.model_dump(),
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info("Async job created: %s", data.get("job_id"))
            
            return CrewAsyncRunResponse(**data)
            
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
        
    except Exception as e:
        logger.exception("Unexpected error in crewai async proxy")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        ) from e


@router.get(
    "/status/{job_id}",
    response_model=CrewStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check crew job status",
)
async def get_crew_status(
    job_id: Annotated[str, Path(..., description="Job ID from async execution")]
) -> CrewStatusResponse:
    """
    Check the status of an async crew job.
    
    Job statuses:
    - **pending**: Job queued, not started yet
    - **running**: Job currently executing
    - **completed**: Job finished successfully (result available)
    - **failed**: Job failed with error
    
    Poll this endpoint to monitor job progress. When status is 'completed',
    the 'result' field contains the final summary.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{CREWAI_URL}/status/{job_id}")  # No prefix
            response.raise_for_status()
            return CrewStatusResponse(**response.json())
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            ) from e
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
        
    except Exception as e:
        logger.exception("Unexpected error getting job status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}",
        ) from e


@router.get(
    "/jobs",
    response_model=list[CrewStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="List recent crew jobs",
)
async def list_crew_jobs(limit: int = 20) -> list[CrewStatusResponse]:
    """
    List recent crew jobs.
    
    Returns up to {limit} most recent jobs, sorted by creation time (newest first).
    Useful for monitoring and debugging async job execution.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{CREWAI_URL}/jobs",  # No prefix
                params={"limit": limit}
            )
            response.raise_for_status()
            return [CrewStatusResponse(**job) for job in response.json()]
            
    except httpx.RequestError as e:
        logger.error("Failed to reach CrewAI service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CrewAI service unavailable: {str(e)}",
        ) from e
        
    except Exception as e:
        logger.exception("Unexpected error listing jobs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}",
        ) from e