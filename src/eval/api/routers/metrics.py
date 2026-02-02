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
        evaluation = await client.evaluate_async(
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
            guardrails=None,
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
    "/summary",
    status_code=status.HTTP_200_OK,
    summary="Get aggregate evaluation statistics",
)
def get_summary():
    """
    Get aggregate statistics across all evaluations.
    
    Returns:
    - Total evaluation count
    - Average scores across all metrics
    - Average performance metrics
    - Success rates
    """
    try:
        logger.info("Summary statistics requested")
        
        db = get_database()
        
        with db.get_session() as session:
            from ...models import EvaluationRecord, EvaluationScores, PerformanceMetrics
            from sqlalchemy import func

            # Get TruLens metrics
            trulens_stats = session.query(
                func.count(EvaluationScores.id).label('total'),
                func.avg(EvaluationScores.overall_score).label('avg_overall'),
                func.avg(EvaluationScores.groundedness).label('avg_groundedness'),
                func.avg(EvaluationScores.answer_relevance).label('avg_answer_relevance'),
                func.avg(EvaluationScores.context_relevance).label('avg_context_relevance'),
            ).first()
            
            # Get Performance metrics
            perf_stats = session.query(
                func.avg(PerformanceMetrics.total_time).label('avg_total_time'),
                func.avg(PerformanceMetrics.rag_retrieval_time).label('avg_rag_time'),
                func.avg(PerformanceMetrics.agent_writer_time).label('avg_agent_time'),
                func.avg(PerformanceMetrics.llm_inference_time).label('avg_llm_time'),
            ).first()
            
            total_count = session.query(func.count(EvaluationRecord.record_id)).scalar() or 0
            
            if total_count == 0:
                return {
                    "total_evaluations": 0,
                    "average_overall_score": 0.0,
                    "average_groundedness": 0.0,
                    "average_answer_relevance": 0.0,
                    "average_context_relevance": 0.0,
                    "average_total_time": 0.0,
                    "average_rag_time": 0.0,
                    "average_agent_time": 0.0,
                    "average_llm_time": 0.0,
                    "total_guardrail_checks": 0,
                    "guardrail_violations": 0,
                    "guardrails_enabled": True,
                }
            
            return {
                "total_evaluations": trulens_stats.total or 0,
                "average_overall_score": round(float(trulens_stats.avg_overall or 0), 3),
                "average_groundedness": round(float(trulens_stats.avg_groundedness or 0), 3),
                "average_answer_relevance": round(float(trulens_stats.avg_answer_relevance or 0), 3),
                "average_context_relevance": round(float(trulens_stats.avg_context_relevance or 0), 3),
                "average_total_time": round(float(perf_stats.avg_total_time or 0), 2),
                "average_rag_time": round(float(perf_stats.avg_rag_time or 0), 2),
                "average_agent_time": round(float(perf_stats.avg_agent_time or 0), 2),
                "average_llm_time": round(float(perf_stats.avg_llm_time or 0), 2),
                "total_guardrail_checks": total_count * 2,  # Input + output
                "guardrail_violations": 0,  # TODO: Get from guardrails table
                "guardrails_enabled": True,
            }
            
    except Exception as e:
        logger.exception("Failed to fetch summary")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch summary: {str(e)}",
        ) from e


@router.get(
    "/recent",
    status_code=status.HTTP_200_OK,
    summary="Get recent evaluations",
)
def get_recent(limit: int = Query(default=10, ge=1, le=100)):
    """
    Get most recent evaluation records.
    
    Args:
        limit: Maximum number of records to return (1-100)
        
    Returns:
        List of recent evaluations with basic info
    """
    try:
        logger.info("Recent evaluations requested (limit=%d)", limit)
        
        db = get_database()
        
        with db.get_session() as session:
            from ...models import EvaluationRecord
            
            records = (
                session.query(EvaluationRecord)
                .order_by(EvaluationRecord.ts.desc())
                .limit(limit)
                .all()
            )
            
            evaluations = []
            for record in records:
                evaluations.append({
                    "record_id": record.record_id,
                    "timestamp": record.ts.isoformat() if record.ts else None,
                    "query": record.input[:100] + "..." if len(record.input) > 100 else record.input,
                    "answer_preview": record.output[:100] + "..." if len(record.output) > 100 else record.output,
                    "app_id": record.app_id,
                })
            
            return {
                "total": len(evaluations),
                "limit": limit,
                "evaluations": evaluations
            }
            
    except Exception as e:
        logger.exception("Failed to fetch recent evaluations")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent evaluations: {str(e)}",
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

        db = get_database()
        
        with db.get_session() as session:
            from ...models import EvaluationRecord, EvaluationScores, PerformanceMetrics
            
            # Join all tables to get complete data
            query = (
                session.query(EvaluationRecord, EvaluationScores, PerformanceMetrics)
                .join(
                    EvaluationScores,
                    EvaluationRecord.record_id == EvaluationScores.record_id
                )
                .outerjoin(
                    PerformanceMetrics,
                    EvaluationRecord.record_id == PerformanceMetrics.record_id
                )
                .order_by(EvaluationScores.overall_score.desc())
            )
            
            if app_id:
                query = query.filter(EvaluationRecord.app_id == app_id)
            
            results = query.limit(limit).all()
            
            # Convert to leaderboard entries
            from datetime import datetime
            
            entries = []
            for record, scores, perf in results:
                entries.append(
                    LeaderboardEntry(
                        record_id=record.record_id,
                        timestamp=record.ts if record.ts else datetime.now(),
                        query=record.input,
                        overall_score=scores.overall_score if scores else 0.0,
                        groundedness=scores.groundedness if scores else 0.0,
                        answer_relevance=scores.answer_relevance if scores else 0.0,
                        context_relevance=scores.context_relevance if scores else 0.0,
                        total_time=perf.total_time if perf else None,
                    )
                )
            
            total_records = session.query(EvaluationRecord).count()
            
            return LeaderboardResponse(
                total_records=total_records,
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
            passed=True,
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
            trulens=None,
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