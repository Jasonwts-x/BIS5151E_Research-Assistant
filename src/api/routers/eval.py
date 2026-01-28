"""
Evaluation Service Router - API Gateway Proxy

Proxies evaluation requests to the evaluation service.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, status

# Import schemas from eval service (avoid duplication)
from ...eval.schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    LeaderboardResponse,
)
from ..openapi import APITag

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/eval", tags=[APITag.EVAL])

# Get eval service URL from environment
EVAL_URL = os.getenv("EVAL_SERVICE_URL", "http://eval:8502")

logger.info("Eval router configured: eval_url=%s", EVAL_URL)


# ============================================================================
# Health Endpoints
# ============================================================================


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Check evaluation service health",
)
async def health():
    """
    Proxy health check to evaluation service.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{EVAL_URL}/health")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error("Eval service unreachable: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Evaluation service unavailable: {str(e)}",
        ) from e
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Check evaluation service readiness",
)
async def ready():
    """
    Proxy readiness check to evaluation service.
    
    Checks if evaluation service is ready to accept requests.
    Verifies database connectivity and TruLens initialization.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{EVAL_URL}/health/ready")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error("Eval service unreachable: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Evaluation service unavailable: {str(e)}",
        ) from e
    except httpx.HTTPStatusError as e:
        logger.error("Eval service not ready: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e


# ============================================================================
# Evaluation Endpoints
# ============================================================================


@router.post(
    "/evaluate",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate a query/answer pair",
)
async def evaluate(request: EvaluationRequest) -> EvaluationResponse:
    """
    Evaluate a query/answer pair with full metrics.
    
    Forwards request to evaluation service which returns:
    - TruLens scores (groundedness, relevance)
    - Guardrails validation results  
    - Quality metrics (ROUGE, BLEU, similarity)
    - Performance metrics
    
    This endpoint is useful for:
    - Testing evaluation metrics on specific outputs
    - Comparing different answer variations
    - Debugging quality issues
    """
    try:
        logger.info("Proxying evaluation request to eval service")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{EVAL_URL}/metrics/evaluate",
                json=request.model_dump(),
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Evaluation completed: record_id=%s", result.get("record_id"))
            
            return EvaluationResponse(**result)
            
    except httpx.HTTPStatusError as e:
        logger.error("Eval service returned error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Evaluation service error: {e.response.text}",
        ) from e
        
    except httpx.RequestError as e:
        logger.error("Failed to reach eval service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Evaluation service unavailable: {str(e)}",
        ) from e


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get evaluation leaderboard",
)
async def leaderboard(
    limit: int = Query(default=100, ge=1, le=1000),
    app_id: Optional[str] = Query(default=None),
) -> LeaderboardResponse:
    """
    Get leaderboard of all evaluations sorted by score.
    
    Shows top-performing queries based on overall evaluation scores.
    Useful for:
    - Identifying best-performing prompts
    - Comparing query variations
    - Quality monitoring over time
    """
    try:
        logger.info("Fetching evaluation leaderboard (limit=%d)", limit)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {"limit": limit}
            if app_id:
                params["app_id"] = app_id
                
            response = await client.get(
                f"{EVAL_URL}/metrics/leaderboard",
                params=params,
            )
            response.raise_for_status()
            
            return LeaderboardResponse(**response.json())
            
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Evaluation service unavailable: {str(e)}",
        ) from e


@router.get(
    "/record/{record_id}",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get evaluation record by ID",
)
async def get_record(record_id: str) -> EvaluationResponse:
    """
    Get detailed evaluation metrics for a specific record.
    
    Returns all metrics including:
    - TruLens scores
    - Guardrails results
    - Performance metrics
    - Quality metrics
    """
    try:
        logger.info("Fetching evaluation record: %s", record_id)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{EVAL_URL}/metrics/record/{record_id}")
            response.raise_for_status()
            
            return EvaluationResponse(**response.json())
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation record not found: {record_id}",
            ) from e
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Evaluation service unavailable: {str(e)}",
        ) from e