from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

# Import SHARED schemas from main API
from ....api.schemas.crewai import CrewRunRequest, CrewRunResponse
from ...runner import get_crew_runner

logger = logging.getLogger(__name__)

router = APIRouter()

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
    "/crew/run",
    response_model=CrewRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute CrewAI workflow (Writer → Reviewer → FactChecker)",
)
def run_crew(request: CrewRunRequest) -> CrewRunResponse:
    """
    Execute the CrewAI research workflow.
    
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
            "Received crew run request: topic='%s', language='%s'",
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


# TODO (Step H): Add translation endpoint if needed
# TODO (Optional): Add /crew/status endpoint for async job tracking