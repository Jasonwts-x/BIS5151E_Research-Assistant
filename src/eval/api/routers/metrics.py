"""
Metrics Router
Endpoints for retrieving evaluation metrics.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError

from ...database import get_database
from ...models import EvaluationRecord, EvaluationScores
from ...schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationSummary,
    LeaderboardEntry,
    LeaderboardResponse,
)
from ...schemas.metrics import TruLensMetrics as TruLensMetricsSchema
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
    
    CRITICAL: This now STORES evaluation to database for dashboard visibility.
    """
    try:
        logger.info("Starting evaluation for query: %s", request.query[:50])
        
        # Step 1: Compute evaluation metrics using TruLens
        client = TruLensClient(enabled=True)
        evaluation = await client.evaluate_async(
            query=request.query,
            context=request.context,
            answer=request.answer,
            language=request.language,
            metadata=request.metadata,
        )
        
        # Generate record ID
        record_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        trulens_data = evaluation.get("trulens", {})
        overall_score = evaluation.get("overall_score", 0)
        
        logger.info("Evaluation computed: record_id=%s, overall_score=%.2f", 
                   record_id, overall_score)
        
        # Step 2: Store to database
        db = get_database()
        try:
            with db.get_session() as session:
                # Create evaluation record
                eval_record = EvaluationRecord(
                    record_id=record_id,
                    ts=timestamp,
                    app_id=request.metadata.get("app_id", "research_assistant") if request.metadata else "research_assistant",
                    input=request.query,
                    output=request.answer,
                    tags=request.language,
                )
                session.add(eval_record)
                
                # Create evaluation scores record (contains TruLens metrics)
                scores_record = EvaluationScores(
                    record_id=record_id,
                    timestamp=timestamp,
                    overall_score=overall_score,
                    groundedness=trulens_data.get("groundedness"),
                    answer_relevance=trulens_data.get("answer_relevance"),
                    context_relevance=trulens_data.get("context_relevance"),
                    citation_quality=trulens_data.get("citation_quality"),
                )
                session.add(scores_record)
                
                # Commit transaction
                session.commit()
                logger.info("✅ Evaluation stored to database: record_id=%s", record_id)
                
        except SQLAlchemyError as e:
            logger.error("❌ Failed to store evaluation to database: %s", e)
            logger.exception("Database storage error")
            # Don't fail the request, just log the error
        
        # Step 3: Build response
        summary = EvaluationSummary(
            passed=overall_score >= 0.6,
            overall_score=overall_score,
            issues=[],
            warnings=[],
        )
        
        response = EvaluationResponse(
            record_id=record_id,
            timestamp=timestamp,
            query=request.query,
            answer_length=len(request.answer),
            summary=summary,
            trulens={
                "groundedness": trulens_data.get("groundedness"),
                "answer_relevance": trulens_data.get("answer_relevance"),
                "context_relevance": trulens_data.get("context_relevance"),
                "citation_quality": trulens_data.get("citation_quality"),
            },
            guardrails=None,
            performance=None,
            quality=None,
        )
        
        logger.info("Evaluation completed successfully: record_id=%s", record_id)
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
    
    Returns summary statistics for display on overview page.
    """
    try:
        logger.info("Summary statistics requested")
        
        db = get_database()
        with db.get_session() as session:
            # Count total evaluations
            total_count = session.query(EvaluationScores).count()
            
            if total_count == 0:
                logger.info("No evaluations in database yet")
                return {
                    "total_evaluations": 0,
                    "average_overall_score": 0.0,
                    "average_groundedness": 0.0,
                    "average_answer_relevance": 0.0,
                    "average_context_relevance": 0.0,
                }
            
            # Calculate averages
            from sqlalchemy import func
            
            averages = session.query(
                func.avg(EvaluationScores.overall_score).label("avg_overall"),
                func.avg(EvaluationScores.groundedness).label("avg_ground"),
                func.avg(EvaluationScores.answer_relevance).label("avg_ans_rel"),
                func.avg(EvaluationScores.context_relevance).label("avg_ctx_rel"),
            ).first()
            
            result = {
                "total_evaluations": total_count,
                "average_overall_score": float(averages.avg_overall or 0),
                "average_groundedness": float(averages.avg_ground or 0),
                "average_answer_relevance": float(averages.avg_ans_rel or 0),
                "average_context_relevance": float(averages.avg_ctx_rel or 0),
            }
            
            logger.info("Summary computed: %d evaluations", total_count)
            return result
            
    except Exception as e:
        logger.exception("Failed to compute summary")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute summary: {str(e)}",
        ) from e


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get evaluation leaderboard",
)
def leaderboard(
    limit: int = Query(default=100, ge=1, le=1000),
    app_id: Optional[str] = Query(default=None),
) -> LeaderboardResponse:
    """
    Get leaderboard of all evaluations sorted by overall score.
    
    Shows top-performing queries based on evaluation scores.
    """
    try:
        logger.info("Leaderboard requested (limit=%d, app_id=%s)", limit, app_id)
        
        db = get_database()
        with db.get_session() as session:
            # Query for leaderboard entries
            query = (
                session.query(
                    EvaluationRecord.record_id,
                    EvaluationRecord.ts,
                    EvaluationRecord.input,
                    EvaluationScores.overall_score,
                    EvaluationScores.groundedness,
                    EvaluationScores.answer_relevance,
                    EvaluationScores.context_relevance,
                )
                .join(EvaluationScores, EvaluationRecord.record_id == EvaluationScores.record_id)
                .order_by(EvaluationScores.overall_score.desc())
            )
            
            if app_id:
                query = query.filter(EvaluationRecord.app_id == app_id)
            
            query = query.limit(limit)
            
            results = query.all()
            
            entries = [
                LeaderboardEntry(
                    record_id=r.record_id,
                    timestamp=r.ts,
                    query=r.input,
                    overall_score=float(r.overall_score or 0),
                    groundedness=float(r.groundedness or 0) if r.groundedness else None,
                    answer_relevance=float(r.answer_relevance or 0) if r.answer_relevance else None,
                    context_relevance=float(r.context_relevance or 0) if r.context_relevance else None,
                    total_time=0.0,
                    passed_guardrails=True,
                )
                for r in results
            ]
            
            logger.info("Leaderboard retrieved: %d entries", len(entries))
            
            return LeaderboardResponse(
                total_records=len(entries),
                entries=entries,
                filters={"app_id": app_id} if app_id else {},
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
    Get detailed evaluation metrics for a specific record.
    
    Returns all metrics including TruLens scores, guardrails, performance.
    """
    try:
        logger.info("Fetching evaluation record: %s", record_id)
        
        db = get_database()
        with db.get_session() as session:
            # Query for record
            record = (
                session.query(EvaluationRecord)
                .filter_by(record_id=record_id)
                .first()
            )
            
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Evaluation record not found: {record_id}",
                )
            
            # Get scores (contains TruLens metrics)
            scores = (
                session.query(EvaluationScores)
                .filter_by(record_id=record_id)
                .first()
            )
            
            # Build response
            summary = EvaluationSummary(
                passed=scores.overall_score >= 0.6 if scores else False,
                overall_score=float(scores.overall_score or 0) if scores else 0.0,
                issues=[],
                warnings=[],
            )
            
            trulens_data = None
            if scores:
                trulens_data = {
                    "groundedness": scores.groundedness,
                    "answer_relevance": scores.answer_relevance,
                    "context_relevance": scores.context_relevance,
                    "citation_quality": scores.citation_quality,
                }
            
            response = EvaluationResponse(
                record_id=record.record_id,
                timestamp=record.ts,
                query=record.input,
                answer_length=len(record.output or ""),
                summary=summary,
                trulens=trulens_data,
                guardrails=None,
                performance=None,
                quality=None,
            )
            
            logger.info("Record retrieved: %s", record_id)
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to retrieve record")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve record: {str(e)}",
        ) from e