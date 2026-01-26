"""
Paraphrase Stability Metric
Measures consistency of evaluation across paraphrased queries.
"""
from __future__ import annotations

import logging
from typing import Callable, List

logger = logging.getLogger(__name__)


class ParaphraseStabilityCalculator:
    """
    Calculate paraphrase stability.
    
    Measures how much evaluation scores vary when the same
    question is asked in different ways.
    """

    def __init__(self, evaluator: Callable):
        """
        Initialize calculator.

        Args:
            evaluator: Function that evaluates (query, context, answer) -> score
        """
        self.evaluator = evaluator

    def calculate(
        self,
        query_variations: List[str],
        context: str,
        answer: str,
        threshold: float = 0.2,
    ) -> dict:
        """
        Calculate paraphrase stability.

        Args:
            query_variations: List of paraphrased versions of same query
            context: Retrieved context (same for all)
            answer: Generated answer (same for all)
            threshold: Maximum acceptable score difference

        Returns:
            Dictionary with stability metrics
        """
        if len(query_variations) < 2:
            logger.warning("Need at least 2 query variations for paraphrase stability")
            return {"stable": True, "max_diff": 0.0, "variations": len(query_variations)}

        # Evaluate each variation
        scores = []
        for query in query_variations:
            try:
                score = self.evaluator(query, context, answer)
                scores.append(score)
            except Exception as e:
                logger.error("Evaluation failed for variation: %s", e)

        if not scores:
            return {"stable": False, "error": "All evaluations failed"}

        # Calculate difference
        min_score = min(scores)
        max_score = max(scores)
        max_diff = max_score - min_score
        is_stable = max_diff < threshold

        logger.info(
            "Paraphrase stability: max_diff=%.3f, stable=%s (%d variations)",
            max_diff,
            is_stable,
            len(scores),
        )

        return {
            "stable": is_stable,
            "max_diff": float(max_diff),
            "min_score": float(min_score),
            "max_score": float(max_score),
            "mean_score": float(sum(scores) / len(scores)),
            "scores": scores,
            "variations": len(scores),
            "threshold": threshold,
        }