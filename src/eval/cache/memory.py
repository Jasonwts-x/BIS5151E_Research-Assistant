"""
In-Memory Cache
Local caching for single-instance deployments.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class EvaluationCache:
    """
    In-memory cache for evaluation results.
    
    Caches by query+answer hash to avoid re-evaluating identical inputs.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of cached items
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.enabled = True
        logger.info("EvaluationCache initialized (max_size=%d)", max_size)

    def _make_key(self, query: str, answer: str, context: str = "") -> str:
        """Generate cache key from inputs."""
        combined = f"{query}|{answer}|{context}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def get(
        self,
        query: str,
        answer: str,
        context: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached evaluation result.
        
        Args:
            query: User query
            answer: Generated answer
            context: Retrieved context
            
        Returns:
            Cached result or None
        """
        if not self.enabled:
            return None

        key = self._make_key(query, answer, context)
        result = self._cache.get(key)

        if result:
            logger.debug("Cache hit for key: %s", key)
        else:
            logger.debug("Cache miss for key: %s", key)

        return result

    def set(
        self,
        query: str,
        answer: str,
        result: Dict[str, Any],
        context: str = "",
    ):
        """
        Store evaluation result in cache.
        
        Args:
            query: User query
            answer: Generated answer
            result: Evaluation result to cache
            context: Retrieved context
        """
        if not self.enabled:
            return

        key = self._make_key(query, answer, context)

        # Implement LRU eviction if cache is full
        if len(self._cache) >= self.max_size:
            # Remove oldest item (first item in dict)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug("Cache eviction: removed %s", oldest_key)

        self._cache[key] = result
        logger.debug("Cache set for key: %s", key)

    def clear(self):
        """Clear all cached results."""
        self._cache.clear()
        logger.info("Cache cleared")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "enabled": self.enabled,
        }


# Singleton
_cache = None


def get_cache() -> EvaluationCache:
    """Get singleton cache instance."""
    global _cache
    if _cache is None:
        _cache = EvaluationCache()
    return _cache