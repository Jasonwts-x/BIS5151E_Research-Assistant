"""
Eval Schemas - Gateway Re-export.

Re-exports Eval schemas from the evaluation service for gateway use.
This provides a single import point for gateway routers.

Architecture Note:
    The actual schema definitions live in src/eval/schemas/evaluation.py.
    This file exists to maintain clean import paths in the API gateway.
"""
from __future__ import annotations

from ...eval.schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    LeaderboardResponse,
)

__all__ = [
    "EvaluationRequest",
    "EvaluationResponse",
    "LeaderboardResponse",
]