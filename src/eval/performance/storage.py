"""
Performance Storage
Store performance metrics to database.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PerformanceStorage:
    """
    Store performance metrics to PostgreSQL.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize storage.

        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self.enabled = database_url is not None

        if self.enabled:
            logger.info("PerformanceStorage initialized with database")
        else:
            logger.info("PerformanceStorage initialized without database (logging only)")

    def store_metrics(
        self,
        record_id: str,
        metrics: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store performance metrics to database.

        Args:
            record_id: Evaluation record ID
            metrics: Performance metrics
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if not self.enabled:
            logger.debug("Storage disabled, logging metrics: %s", metrics)
            return False

        try:
            from ..database import get_database
            from ..models import PerformanceMetrics

            db = get_database()

            # Extract metrics
            perf_data = PerformanceMetrics(
                record_id=record_id,
                timestamp=datetime.utcnow(),
                total_time=metrics.get("total_time"),
                rag_retrieval_time=metrics.get("rag_retrieval"),
                agent_writer_time=metrics.get("agent_writer"),
                agent_reviewer_time=metrics.get("agent_reviewer"),
                agent_factchecker_time=metrics.get("agent_factchecker"),
                llm_inference_time=metrics.get("llm_inference"),
                guardrails_time=metrics.get("guardrails_input", 0)
                + metrics.get("guardrails_output", 0),
                evaluation_time=metrics.get("trulens_evaluation"),
                model_name=metadata.get("model") if metadata else None,
                language=metadata.get("language") if metadata else None,
            )

            with db.get_session() as session:
                session.add(perf_data)
                session.commit()

            logger.info(
                "Stored performance metrics for record %s: total_time=%.2fs",
                record_id,
                metrics.get("total_time", 0),
            )
            return True

        except Exception as e:
            logger.error("Failed to store performance metrics: %s", e)
            return False

    def get_metrics(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metrics for a specific record.

        Args:
            record_id: Evaluation record ID

        Returns:
            Metrics dictionary or None
        """
        if not self.enabled:
            return None

        try:
            from ..database import get_database
            from ..models import PerformanceMetrics

            db = get_database()

            with db.get_session() as session:
                result = (
                    session.query(PerformanceMetrics)
                    .filter_by(record_id=record_id)
                    .first()
                )

                if result:
                    return {
                        "total_time": result.total_time,
                        "rag_retrieval": result.rag_retrieval_time,
                        "agent_writer": result.agent_writer_time,
                        "agent_reviewer": result.agent_reviewer_time,
                        "agent_factchecker": result.agent_factchecker_time,
                        "llm_inference": result.llm_inference_time,
                        "guardrails": result.guardrails_time,
                        "evaluation": result.evaluation_time,
                    }

            return None

        except Exception as e:
            logger.error("Failed to retrieve performance metrics: %s", e)
            return None

    def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregate statistics over time period.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Statistics dictionary
        """
        if not self.enabled:
            return {}

        try:
            from sqlalchemy import func

            from ..database import get_database
            from ..models import PerformanceMetrics

            db = get_database()

            with db.get_session() as session:
                query = session.query(
                    func.count(PerformanceMetrics.id).label("count"),
                    func.avg(PerformanceMetrics.total_time).label("avg_total_time"),
                    func.min(PerformanceMetrics.total_time).label("min_total_time"),
                    func.max(PerformanceMetrics.total_time).label("max_total_time"),
                )

                if start_date:
                    query = query.filter(PerformanceMetrics.timestamp >= start_date)
                if end_date:
                    query = query.filter(PerformanceMetrics.timestamp <= end_date)

                result = query.first()

                if result:
                    return {
                        "total_records": result.count or 0,
                        "avg_total_time": float(result.avg_total_time or 0),
                        "min_total_time": float(result.min_total_time or 0),
                        "max_total_time": float(result.max_total_time or 0),
                    }

            return {}

        except Exception as e:
            logger.error("Failed to retrieve statistics: %s", e)
            return {}