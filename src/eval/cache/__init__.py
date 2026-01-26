"""
Evaluation Cache Module
In-memory and Redis-based caching for evaluation results.
"""
from __future__ import annotations

from .memory import EvaluationCache, get_cache
from .redis import RedisCache, get_redis_cache

__all__ = [
    "EvaluationCache",
    "get_cache",
    "RedisCache",
    "get_redis_cache",
]