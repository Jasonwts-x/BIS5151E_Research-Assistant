"""
TruLens Client
Client for communicating with evaluation service.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..cache import get_cache, get_redis_cache

logger = logging.getLogger(__name__)


class TruLensClient:
    """
    Client for TruLens evaluation service.

    Sends evaluation requests and stores results in database.
    """

    def __init__(self, base_url: str = "http://eval:8502", enabled: bool = True):
        """
        Initialize client.

        Args:
            base_url: Base URL of evaluation service
            enabled: Whether client is enabled
        """
        self.base_url = base_url
        self.enabled = enabled
        logger.info("TruLensClient initialized: %s (enabled=%s)", base_url, enabled)

        redis_enabled = os.getenv("REDIS_URL") is not None
        if redis_enabled:
            self.cache = get_redis_cache()
            logger.info("Using Redis cache for evaluations")
        else:
            self.cache = get_cache()
            logger.info("Using in-memory cache for evaluations")

    def evaluate(
        self,
        query: str,
        context: str,
        answer: str,
        language: str = "en",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send evaluation request and store in database.

        Args:
            query: User query
            context: Retrieved context
            answer: Generated answer
            language: Language code
            metadata: Optional metadata

        Returns:
            Evaluation results
        """
        if not self.enabled:
            logger.debug("TruLens client disabled, skipping evaluation")
            return {"enabled": False}
        
        cached = self.cache.get(query, answer, context)
        if cached:
            logger.info("Returning cached evaluation result")
            return cached

        record_id = str(uuid4())

        # Use local feedback provider
        from .feedback import FeedbackProvider

        provider = FeedbackProvider()

        groundedness, ground_reason = provider.groundedness_score(context, answer)
        relevance, rel_reason = provider.relevance_score(query, answer)
        context_rel, ctx_reason = provider.context_relevance_score(query, context)
        citation_qual, cite_reason = provider.citation_quality_score(answer)

        result = {
            "record_id": record_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "answer_length": len(answer),
            "trulens": {
                "groundedness": groundedness,
                "groundedness_reasoning": ground_reason,
                "answer_relevance": relevance,
                "answer_relevance_reasoning": rel_reason,
                "context_relevance": context_rel,
                "context_relevance_reasoning": ctx_reason,
                "citation_quality": citation_qual,
                "citation_quality_reasoning": cite_reason,
            },
            "overall_score": (groundedness + relevance + context_rel + citation_qual) / 4,
        }

        # Store in database
        try:
            self._store_to_database(record_id, query, answer, result, metadata)
        except Exception as e:
            logger.error("Failed to store evaluation to database: %s", e)

        self.cache.set(query, answer, result, context)

        logger.info(
            "Evaluation complete: record_id=%s, overall_score=%.2f",
            record_id,
            result["overall_score"],
        )

        return result
    
    async def evaluate_async(
        self,
        query: str,
        context: str,
        answer: str,
        language: str = "en",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Async version of evaluate().
        
        Use this when calling from async code to avoid blocking.
        """
        if not self.enabled:
            return {"enabled": False}

        # Check cache
        cached = self.cache.get(query, answer, context)
        if cached:
            return cached

        # Run evaluation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.evaluate,
            query,
            context,
            answer,
            language,
            metadata,
        )

        return result

    def _store_to_database(
        self,
        record_id: str,
        query: str,
        answer: str,
        evaluation: Dict[str, Any],
        metadata: Optional[Dict[str, Any]],
    ):
        """Store evaluation to database."""
        try:
            from ..database import get_database
            from ..models import EvaluationRecord, EvaluationScores
    
            db = get_database()
    
            # Create evaluation record
            record = EvaluationRecord(
                record_id=record_id,
                ts=datetime.utcnow(),
                app_id=metadata.get("app_id", "research-assistant") if metadata else "research-assistant",
                input=query,
                output=answer,
                tags=metadata.get("tags") if metadata else None,
            )
    
            # Create scores record
            trulens_data = evaluation.get("trulens", {})
            scores = EvaluationScores(
                record_id=record_id,
                overall_score=evaluation.get("overall_score", 0.0),
                groundedness=trulens_data.get("groundedness", 0.0),
                answer_relevance=trulens_data.get("answer_relevance", 0.0),
                context_relevance=trulens_data.get("context_relevance", 0.0),
                citation_quality=trulens_data.get("citation_quality", 0.0),
            )
    
            with db.get_session() as session:
                session.add(record)
                session.add(scores)
                session.commit()
                logger.info("✓ Stored evaluation record %s with scores to database", record_id)
    
        except Exception as e:
            logger.error("Failed to store evaluation to database: %s", e, exc_info=True)
            # Don't raise - evaluation storage failures shouldn't break the main workflow

    def get_leaderboard(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get evaluation leaderboard from database.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of evaluation records sorted by overall score
        """
        if not self.enabled:
            return []

        try:
            from sqlalchemy import desc

            from ..database import get_database
            from ..models import EvaluationRecord, PerformanceMetrics

            db = get_database()

            with db.get_session() as session:
                # Query recent records with performance data
                results = (
                    session.query(EvaluationRecord, PerformanceMetrics)
                    .outerjoin(PerformanceMetrics, EvaluationRecord.record_id == PerformanceMetrics.record_id)
                    .order_by(desc(EvaluationRecord.ts))
                    .limit(limit)
                    .all()
                )

                leaderboard = []
                for record, perf in results:
                    leaderboard.append(
                        {
                            "record_id": record.record_id,
                            "timestamp": record.ts.isoformat(),
                            "query": record.input[:100] + "..." if len(record.input) > 100 else record.input,
                            "total_time": perf.total_time if perf else None,
                        }
                    )

                return leaderboard

        except Exception as e:
            logger.error("Failed to retrieve leaderboard: %s", e)
            return []

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific evaluation record from database.

        Args:
            record_id: Record ID

        Returns:
            Evaluation record or None
        """
        if not self.enabled:
            return None

        try:
            from ..database import get_database
            from ..models import EvaluationRecord, PerformanceMetrics, QualityMetrics

            db = get_database()

            with db.get_session() as session:
                record = (
                    session.query(EvaluationRecord)
                    .filter_by(record_id=record_id)
                    .first()
                )

                if not record:
                    return None

                # Get related metrics
                perf = (
                    session.query(PerformanceMetrics)
                    .filter_by(record_id=record_id)
                    .first()
                )
                quality = (
                    session.query(QualityMetrics)
                    .filter_by(record_id=record_id)
                    .first()
                )

                result = {
                    "record_id": record.record_id,
                    "timestamp": record.ts.isoformat(),
                    "query": record.input,
                    "answer": record.output,
                }

                if perf:
                    result["performance"] = {
                        "total_time": perf.total_time,
                        "rag_retrieval": perf.rag_retrieval_time,
                        "llm_inference": perf.llm_inference_time,
                    }

                if quality:
                    result["quality"] = {
                        "rouge_1": quality.rouge_1,
                        "rouge_2": quality.rouge_2,
                        "bleu_score": quality.bleu_score,
                    }

                return result

        except Exception as e:
            logger.error("Failed to retrieve record: %s", e)
            return None