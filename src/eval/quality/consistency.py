"""
Consistency Metric
Measures variance in evaluation scores across multiple runs.
"""
from __future__ import annotations

import logging
from typing import List

import numpy as np

logger = logging.getLogger(__name__)


class ConsistencyCalculator:
    """
    Calculate consistency metric for multiple runs.
    
    Measures how stable evaluation scores are when running
    the same query multiple times.
    """

    def calculate(
        self,
        scores: List[float],
        threshold: float = 0.15,
    ) -> dict:
        """
        Calculate consistency metric.

        Args:
            scores: List of scores from multiple runs
            threshold: Maximum acceptable standard deviation

        Returns:
            Dictionary with consistency metrics
        """
        if len(scores) < 2:
            return {
                "consistent": True,
                "std_dev": 0.0,
                "mean": scores[0] if scores else 0.0,
                "runs": len(scores),
            }

        mean = np.mean(scores)
        std_dev = np.std(scores)
        is_consistent = std_dev < threshold

        logger.info(
            "Consistency check: mean=%.3f, std_dev=%.3f, consistent=%s",
            mean,
            std_dev,
            is_consistent,
        )

        return {
            "consistent": is_consistent,
            "std_dev": float(std_dev),
            "mean": float(mean),
            "min": float(np.min(scores)),
            "max": float(np.max(scores)),
            "runs": len(scores),
            "threshold": threshold,
        }