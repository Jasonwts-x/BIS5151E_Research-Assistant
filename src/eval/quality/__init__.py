"""
Quality Metrics Module
ROUGE, BLEU, semantic similarity, and factuality checking.
"""
from __future__ import annotations

from .bleu import BLEUCalculator
from .consistency import ConsistencyCalculator
from .factuality import FactualityChecker
from .paraphrase import ParaphraseStabilityCalculator
from .rouge import ROUGECalculator
from .semantic import SemanticSimilarityCalculator
from .storage import store_quality_metrics  # ✨ NEW

__all__ = [
    "ROUGECalculator",
    "BLEUCalculator",
    "SemanticSimilarityCalculator",
    "FactualityChecker",
    "ConsistencyCalculator",
    "ParaphraseStabilityCalculator",
    "store_quality_metrics",  # ✨ NEW
]