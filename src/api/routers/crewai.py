from __future__ import annotations

import logging
import os
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Path, status

from ..openapi import APITag
from ..schemas.crewai import (
    CrewRunRequest,
    CrewRunResponse,
    CrewStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crewai", tags=[APITag.CREWAI])

# CrewAI service URL (internal Docker network)
# Can be overridden via CREWAI_URL environment variable
CREWAI_URL = os.getenv("CREWAI_URL", "http://crewai:8100")


@router.post(
    "/run",
    response_model=CrewRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute CrewAI multi-agent workflow",
)
async def crewai_run(payload: CrewRunRequest) -> CrewRunResponse:
    """
    Execute the CrewAI research workflow via the crewai service.
    
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
            "Proxying crewai run request to %s/crew/run: topic='%s', language='%s'",
            CREWAI_URL,
            payload.topic,
            payload.language,
        )
        
        # Forward request to crewai service
        async with httpx.AsyncClient(timeout=120.0) as client:  # Long timeout for LLM
            response = await client.post(
                f"{CREWAI_URL}/crew/run",
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


@router.get(
    "/status/{job_id}",
    response_model=CrewStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check crew job status (placeholder for future async execution)",
)
async def get_crew_status(
    job_id: Annotated[str, Path(..., description="Job ID from async execution")]
) -> CrewStatusResponse:
    """
    Check the status of an async crew job.
    
    **NOTE: This is a placeholder for future async job tracking (Step D+).**
    **Currently not implemented - will return 501 Not Implemented.**
    
    Future possible statuses:
    - pending: Job queued, not started
    - running: Job currently executing
    - completed: Job finished successfully
    - failed: Job failed with error
    """
    # TODO (Future): Implement async job tracking
    # For now, return not implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Async job tracking not yet implemented. Use synchronous /crewai/run endpoint.",
    )


# TODO (Optional): Add health check proxy endpoint
# @router.get("/health")
# async def crewai_health():
#     """Proxy to crewai service health check"""
#     async with httpx.AsyncClient(timeout=5.0) as client:
#         response = await client.get(f"{CREWAI_SERVICE_URL}/health")
#         return response.json()

# TODO (Optional): Add staus check endpoint for async jobs

# @router.get(
#     "/status/{job_id}",
#     response_model=CrewStatusResponse,
#     status_code=status.HTTP_200_OK,
#     summary="Check crew job status",
# )
# async def get_crew_status(
#     job_id: Annotated[str, Path(..., description="Job ID from async execution")]
# ) -> CrewStatusResponse:
#     """
#     Check the status of an async crew job.
    
#     Possible statuses:
#     - pending: Job queued, not started
#     - running: Job currently executing
#     - completed: Job finished successfully
#     - failed: Job failed with error
#     """
#     logger.info("Checking crew job status: %s", job_id)
    
#     try:
#         async with httpx.AsyncClient(timeout=5.0) as client:
#             response = await client.get(f"{CREW_SERVICE_URL}/status/{job_id}")
#             response.raise_for_status()
#             return CrewStatusResponse(**response.json())
#     except httpx.HTTPStatusError as e:
#         if e.response.status_code == 404:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Job {job_id} not found",
#             ) from e
#         raise
#     except Exception as e:
#         logger.exception("Failed to get crew status")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to get status: {str(e)}",
#         ) from e