"""
CrewAI Service Router.

Endpoints for synchronous and asynchronous crew execution.

Architecture:
    Provides both sync (/run) and async (/run/async) endpoints.
    Async jobs are managed by JobManager and executed in background.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from ...schemas.crewai import (
    CrewAsyncRunResponse,
    CrewRunRequest,
    CrewRunResponse,
    CrewStatusResponse,
)
from ..jobs import get_job_manager
from ...runner import get_crew_runner

logger = logging.getLogger(__name__)

router = APIRouter()

runner = get_crew_runner()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="CrewAI service health check",
)
def health():
    """
    Simple health check endpoint.
    
    Returns:
        Status dictionary
    """
    return {"status": "ok", "service": "crew"}


@router.post(
    "/run",
    response_model=CrewRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute CrewAI workflow synchronously (BLOCKS until complete)",
)
def run_crew_sync(request: CrewRunRequest) -> CrewRunResponse:
    """
    Execute the CrewAI research workflow synchronously.
    
    **WARNING: This endpoint blocks for 30-60 seconds during execution.**
    
    Args:
        request: Crew run request with topic and language
        
    Returns:
        Crew run response with final output and evaluation
        
    Raises:
        HTTPException: If execution fails
    """
    try:
        logger.info(
            "Received synchronous crew run request: topic='%s', language='%s'",
            request.topic,
            request.language,
        )
        
        # Execute crew workflow
        result = runner.run(topic=request.topic, language=request.language)

        # Save outputs to files
        try:
            saved_paths = runner.save_output(result)
            logger.info("Outputs saved: %s", list(saved_paths.keys()))
        except Exception as e:
            logger.warning("Failed to save outputs: %s", e)
        
        return CrewRunResponse(
            topic=result.topic,
            language=result.language,
            answer=result.final_output,
            evaluation=result.evaluation,
        )
        
    except Exception as e:
        logger.exception("Crew execution failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crew execution failed: {str(e)}",
        ) from e


@router.post(
    "/run/async",
    response_model=CrewAsyncRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute CrewAI workflow asynchronously (returns immediately)",
)
async def run_crew_async(
    request: CrewRunRequest,
    background_tasks: BackgroundTasks,
) -> CrewAsyncRunResponse:
    """
    Execute the CrewAI research workflow asynchronously.
    
    **This endpoint returns immediately with a job_id.**

    Use GET /status/{job_id} to check progress and retrieve results.
    
    Args:
        request: Crew run request
        background_tasks: FastAPI background tasks
        
    Returns:
        Async response with job_id for tracking
        
    Raises:
        HTTPException: If job creation fails
    """
    try:
        logger.info(
            "Received async crew run request: topic='%s', language='%s'",
            request.topic,
            request.language,
        )
        
        # Get job manager
        job_manager = get_job_manager()
        
        # Create job
        job_id = job_manager.create_job(
            topic=request.topic,
            language=request.language,
        )
        
        # Schedule background execution
        background_tasks.add_task(
            job_manager.execute_job,
            job_id,
        )
        
        logger.info("Async job created: %s", job_id)
        
        return CrewAsyncRunResponse(
            job_id=job_id,
            status="pending",
            message=f"Job {job_id} created. Use GET /status/{job_id} to check progress.",
        )
        
    except Exception as e:
        logger.exception("Failed to create async job")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create async job: {str(e)}",
        ) from e


@router.get(
    "/status/{job_id}",
    response_model=CrewStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get status of async crew job",
)
def get_job_status(job_id: str) -> CrewStatusResponse:
    """
    Get the status of an async crew job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status with progress and result (if completed)
        
    Raises:
        HTTPException: If job not found
    """
    try:
        logger.info("Status check requested for job: %s", job_id)
        
        # Get job manager
        job_manager = get_job_manager()
        
        # Get job
        job = job_manager.get_job(job_id)
        
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}",
            )
        
        # Build response
        response = CrewStatusResponse(
            job_id=job.job_id,
            status=job.status.value,
            topic=job.topic,
            language=job.language,
            progress=job.progress,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            result=job.result.final_output if job.result else None,
            error=job.error,
        )
        
        if job.result and job.result.evaluation:
            response.evaluation = job.result.evaluation
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get job status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}",
        ) from e