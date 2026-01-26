"""
TruLens Client
Client for communicating with TruLens evaluation service.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class TruLensClient:
    """
    Client for TruLens evaluation service.
    
    Sends evaluation requests to the eval service and retrieves results.
    """

    def __init__(
        self,
        base_url: str = "http://eval:8502",
        enabled: bool = True,
    ):
        """
        Initialize client.

        Args:
            base_url: Base URL of evaluation service
            enabled: Whether client is enabled
        """
        self.base_url = base_url
        self.enabled = enabled
        logger.info("TruLensClient initialized: %s (enabled=%s)", base_url, enabled)

    def evaluate(
        self,
        query: str,
        context: str,
        answer: str,
        language: str = "en",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send evaluation request to service.

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

        # TODO: Implement HTTP request to eval service
        # For now, return mock data
        
        record_id = str(uuid4())
        
        # Use local feedback provider for now
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
        
        logger.info(
            "Evaluation complete: record_id=%s, overall_score=%.2f",
            record_id,
            result["overall_score"],
        )
        
        return result

    def get_leaderboard(
        self,
        limit: int = 100,
    ) -> list[Dict[str, Any]]:
        """
        Get evaluation leaderboard from service.

        Args:
            limit: Maximum number of records

        Returns:
            List of evaluation records
        """
        if not self.enabled:
            return []

        # TODO: Implement HTTP request to eval service
        logger.warning("Leaderboard not yet implemented")
        return []

    def get_record(
        self,
        record_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific evaluation record.

        Args:
            record_id: Record ID

        Returns:
            Record details or None
        """
        if not self.enabled:
            return None

        # TODO: Implement HTTP request to eval service
        logger.warning("Get record not yet implemented")
        return None