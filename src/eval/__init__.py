"""
Evaluation Module
Comprehensive evaluation and monitoring for ResearchAssistantGPT.

Components:
- Guardrails: Input/output validation
- TruLens: Quality metrics (groundedness, relevance)
- Performance: Timing and resource tracking
- Quality: ROUGE, BLEU, semantic similarity
"""
from __future__ import annotations

from .guardrails import (
    GuardrailValidator,
    GuardrailsConfig,
    InputValidator,
    OutputValidator,
    ValidationResult,
    load_guardrails_config,
)
from .performance import PerformanceTracker, track_performance
from .quality import (
    BLEUCalculator,
    FactualityChecker,
    ROUGECalculator,
    SemanticSimilarityCalculator,
)
from .trulens import FeedbackProvider, TruLensClient

__all__ = [
    # Guardrails
    "GuardrailValidator",
    "ValidationResult",
    "GuardrailsConfig",
    "load_guardrails_config",
    "InputValidator",
    "OutputValidator",
    # TruLens
    "TruLensClient",
    "FeedbackProvider",
    # Performance
    "PerformanceTracker",
    "track_performance",
    # Quality
    "ROUGECalculator",
    "BLEUCalculator",
    "SemanticSimilarityCalculator",
    "FactualityChecker",
]