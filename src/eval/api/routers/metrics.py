"""
Metrics Router
Endpoints for retrieving evaluation metrics.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...database import get_database
from ...schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    LeaderboardEntry,
    LeaderboardResponse,
)
from ...trulens import TruLensClient
from ...cache import get_cache, get_redis_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post(
    "/evaluate",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate a query/answer pair",
)
async def evaluate(request: EvaluationRequest) -> EvaluationResponse:
    """
    Evaluate a query/answer pair with full metrics.

    Returns:
    - TruLens scores (groundedness, relevance)
    - Guardrails validation results
    - Quality metrics (ROUGE, BLEU, semantic similarity)
    - Performance metrics (if available)
    """
    try:
        # Evaluate using TruLens client (stores to DB)
        client = TruLensClient(enabled=True)
        evaluation = client.evaluate_async(
            query=request.query,
            context=request.context,
            answer=request.answer,
            language=request.language,
            metadata=request.metadata,
        )

        # Build response
        from datetime import datetime

        from ...schemas.evaluation import EvaluationSummary

        summary = EvaluationSummary(
            passed=evaluation.get("overall_score", 0) >= 0.6,
            overall_score=evaluation.get("overall_score", 0),
            issues=[],
            warnings=[],
        )

        response = EvaluationResponse(
            record_id=evaluation["record_id"],
            timestamp=datetime.now(),
            query=request.query,
            answer_length=len(request.answer),
            summary=summary,
            trulens=evaluation.get("trulens"),
            guardrails=None,  # TODO: Add guardrails results
        )

        logger.info("Evaluation completed: record_id=%s", evaluation["record_id"])
        return response

    except Exception as e:
        logger.exception("Evaluation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        ) from e


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get evaluation leaderboard",
)
def get_leaderboard(
    limit: int = Query(default=100, ge=1, le=1000),
    app_id: Optional[str] = Query(default=None),
) -> LeaderboardResponse:
    """
    Get leaderboard of all evaluations.

    Shows top-performing queries sorted by overall score.
    """
    try:
        logger.info("Leaderboard requested (limit=%d, app_id=%s)", limit, app_id)

        # Get from database
        client = TruLensClient(enabled=True)
        records = client.get_leaderboard(limit=limit)

        # Convert to leaderboard entries
        from datetime import datetime

        entries = [
            LeaderboardEntry(
                record_id=r["record_id"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                query=r["query"],
                overall_score=0.0,  # TODO: Calculate from stored metrics
                total_time=r.get("total_time"),
            )
            for r in records
        ]

        return LeaderboardResponse(
            total_records=len(entries),
            entries=entries,
        )

    except Exception as e:
        logger.exception("Failed to retrieve leaderboard")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve leaderboard: {str(e)}",
        ) from e


@router.get(
    "/record/{record_id}",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get evaluation record by ID",
)
def get_record(record_id: str) -> EvaluationResponse:
    """
    Get detailed evaluation record by ID.

    Returns all metrics and metadata for a specific evaluation.
    """
    try:
        logger.info("Record requested: %s", record_id)

        # Get from database
        client = TruLensClient(enabled=True)
        record = client.get_record(record_id)

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record not found: {record_id}",
            )

        # Convert to response
        from datetime import datetime

        from ...schemas.evaluation import EvaluationSummary

        summary = EvaluationSummary(
            passed=True,  # TODO: Calculate from metrics
            overall_score=0.75,  # TODO: Calculate from stored metrics
            issues=[],
            warnings=[],
        )

        response = EvaluationResponse(
            record_id=record_id,
            timestamp=datetime.fromisoformat(record["timestamp"]),
            query=record["query"],
            answer_length=len(record["answer"]),
            summary=summary,
            trulens=None,  # TODO: Get from DB
            guardrails=None,
            performance=record.get("performance"),
            quality=record.get("quality"),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to retrieve record")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve record: {str(e)}",
        ) from e
    
    
@router.post(
    "/benchmark/consistency",
    status_code=status.HTTP_200_OK,
    summary="Run consistency benchmark",
)
def benchmark_consistency(
    query: str,
    context: str,
    runs: int = 3,
):
    """
    Run consistency benchmark.
    
    Executes the same query multiple times and measures score variance.
    """
    from ...quality import ConsistencyCalculator
    from ...trulens import TruLensClient
    
    client = TruLensClient(enabled=True)
    scores = []
    
    for i in range(runs):
        # Run evaluation (this would need to trigger full pipeline)
        result = client.evaluate(
            query=query,
            context=context,
            answer="",  # Would need actual answer from pipeline
        )
        scores.append(result.get("overall_score", 0))
    
    calculator = ConsistencyCalculator()
    consistency = calculator.calculate(scores)
    
    return consistency


@router.post(
    "/benchmark/paraphrase",
    status_code=status.HTTP_200_OK,
    summary="Run paraphrase stability benchmark",
)
def benchmark_paraphrase(
    query_variations: list[str],
    context: str,
    answer: str,
):
    """
    Run paraphrase stability benchmark.
    
    Tests how evaluation scores vary across paraphrased queries.
    """
    from ...quality import ParaphraseStabilityCalculator
    from ...trulens import FeedbackProvider
    
    provider = FeedbackProvider()
    
    def evaluator(query, context, answer):
        score, _ = provider.groundedness_score(context, answer)
        return score
    
    calculator = ParaphraseStabilityCalculator(evaluator)
    stability = calculator.calculate(query_variations, context, answer)
    
    return stability