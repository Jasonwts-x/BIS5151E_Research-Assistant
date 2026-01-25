from __future__ import annotations


import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from ....api.openapi import APITag
from ....api.schemas.crewai import (
    CrewAsyncRunResponse,
    CrewRunRequest,
    CrewRunResponse,
    CrewStatusResponse,
)
from ..jobs import get_job_manager
from ...runner import get_crew_runner #?

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crewai", tags=[APITag.CREWAI])

# Initialize crew runner (singleton for this service)
runner = get_crew_runner()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="CrewAI service health check",
)
def health():
    """Simple health check endpoint."""
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
    
    For non-blocking execution, use POST /crew/run/async instead.
    
    Steps:
    1. Retrieve relevant context from RAG pipeline
    2. Run Writer agent to draft summary
    3. Run Reviewer agent to improve clarity
    4. Run FactChecker agent to verify claims
    5. Save outputs to outputs/ directory
    6. Return final output
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
    
    Use GET /crew/status/{job_id} to check progress and retrieve results.
    
    Ideal for:
    - Web UIs (show progress indicators)
    - N8N workflows (wait/poll pattern)
    - Batch processing (submit many, collect later)
    """
    try:
        logger.info(
            "Received async crew run request: topic='%s', language='%s'",
            request.topic,
            request.language,
        )
        
        # Get job manager
        manager = get_job_manager()
        
        # Create job
        job_id = manager.create_job(topic=request.topic, language=request.language)
        
        # Schedule background execution
        background_tasks.add_task(manager.execute_job, job_id)
        
        logger.info("Job %s queued for background execution", job_id)
        
        return CrewAsyncRunResponse(
            job_id=job_id,
            status="pending",
            message=f"Job {job_id} created and queued for execution",
        )
        
    except Exception as e:
        logger.exception("Failed to create async job")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}",
        ) from e


@router.get(
    "/status/{job_id}",
    response_model=CrewStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check async crew job status",
)
def get_crew_status(job_id: str) -> CrewStatusResponse:
    """
    Check the status of an async crew job.
    
    Job statuses:
    - **pending**: Job queued, not started yet
    - **running**: Job currently executing
    - **completed**: Job finished successfully (result available)
    - **failed**: Job failed with error
    
    Poll this endpoint to monitor progress.
    """
    try:
        manager = get_job_manager()
        job = manager.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
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
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get job status")
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
def list_jobs(limit: int = 20) -> list[CrewStatusResponse]:
    """
    List recent crew jobs.
    
    Returns up to {limit} most recent jobs, sorted by creation time (newest first).
    """
    try:
        manager = get_job_manager()
        jobs = manager.list_jobs(limit=limit)
        
        return [
            CrewStatusResponse(
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
            for job in jobs
        ]
        
    except Exception as e:
        logger.exception("Failed to list jobs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}",
        ) from e
    
# TODO (Step H): Add translation endpoint if needed