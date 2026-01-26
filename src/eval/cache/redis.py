"""
Redis Cache
Distributed caching using Redis for multi-instance deployments.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based distributed cache for evaluation results.
    
    Use this instead of EvaluationCache when running multiple instances.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        ttl: int = 3600,
    ):
        """
        Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL")

        self.redis_url = redis_url
        self.ttl = ttl
        self.enabled = False
        self.redis_client = None

        if not redis_url:
            logger.info("Redis URL not configured, cache disabled")
            return

        try:
            import redis
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            self.enabled = True
            logger.info("RedisCache initialized: %s (TTL=%ds)", redis_url, ttl)
        except ImportError:
            logger.warning("Redis package not installed. Install with: pip install redis")
        except Exception as e:
            logger.warning("Redis not available: %s. Cache disabled.", e)

    def _make_key(self, query: str, answer: str, context: str = "") -> str:
        """Generate cache key."""
        combined = f"{query}|{answer}|{context}"
        hash_val = hashlib.sha256(combined.encode()).hexdigest()[:16]
        return f"eval:{hash_val}"

    def get(
        self,
        query: str,
        answer: str,
        context: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Get cached evaluation result from Redis."""
        if not self.enabled:
            return None

        try:
            key = self._make_key(query, answer, context)
            data = self.redis_client.get(key)

            if data:
                logger.debug("Redis cache hit: %s", key)
                return json.loads(data)
            else:
                logger.debug("Redis cache miss: %s", key)
                return None

        except Exception as e:
            logger.error("Redis get failed: %s", e)
            return None

    def set(
        self,
        query: str,
        answer: str,
        result: Dict[str, Any],
        context: str = "",
    ):
        """Store evaluation result in Redis."""
        if not self.enabled:
            return

        try:
            key = self._make_key(query, answer, context)
            data = json.dumps(result)
            self.redis_client.setex(key, self.ttl, data)
            logger.debug("Redis cache set: %s (TTL=%ds)", key, self.ttl)

        except Exception as e:
            logger.error("Redis set failed: %s", e)

    def clear(self):
        """Clear all evaluation cache keys."""
        if not self.enabled:
            return

        try:
            # Find all eval: keys
            keys = self.redis_client.keys("eval:*")
            if keys:
                self.redis_client.delete(*keys)
                logger.info("Redis cache cleared: %d keys deleted", len(keys))
        except Exception as e:
            logger.error("Redis clear failed: %s", e)

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}

        try:
            info = self.redis_client.info("stats")
            keys = len(self.redis_client.keys("eval:*"))

            return {
                "enabled": True,
                "keys": keys,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "ttl": self.ttl,
            }
        except Exception as e:
            logger.error("Redis stats failed: %s", e)
            return {"enabled": True, "error": str(e)}


# Singleton
_redis_cache = None


def get_redis_cache() -> RedisCache:
    """Get singleton Redis cache instance."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache