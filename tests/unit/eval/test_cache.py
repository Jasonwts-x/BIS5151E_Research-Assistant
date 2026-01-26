"""Tests for evaluation cache."""
from __future__ import annotations

import pytest

from src.eval.cache import EvaluationCache, get_cache


class TestEvaluationCache:
    """Tests for in-memory evaluation cache."""

    @pytest.fixture
    def cache(self):
        """Create fresh cache instance."""
        return EvaluationCache(max_size=3)

    def test_cache_initialization(self, cache):
        """Test cache initializes with correct settings."""
        assert cache.enabled is True
        assert cache.max_size == 3
        assert len(cache._cache) == 0

    def test_cache_miss(self, cache):
        """Test cache miss returns None."""
        result = cache.get("query", "answer", "context")
        assert result is None

    def test_cache_hit(self, cache):
        """Test cache hit returns stored value."""
        # Store
        evaluation = {"score": 0.85, "passed": True}
        cache.set("query", "answer", evaluation, "context")

        # Retrieve
        result = cache.get("query", "answer", "context")
        assert result == evaluation

    def test_cache_key_generation(self, cache):
        """Test cache key is consistent."""
        key1 = cache._make_key("query", "answer", "context")
        key2 = cache._make_key("query", "answer", "context")
        assert key1 == key2

        # Different inputs produce different keys
        key3 = cache._make_key("query2", "answer", "context")
        assert key1 != key3

    def test_cache_eviction(self, cache):
        """Test LRU eviction when cache is full."""
        # Fill cache
        cache.set("q1", "a1", {"score": 0.8})
        cache.set("q2", "a2", {"score": 0.9})
        cache.set("q3", "a3", {"score": 0.7})

        # Cache is full (max_size=3)
        assert len(cache._cache) == 3

        # Add one more - should evict oldest
        cache.set("q4", "a4", {"score": 0.85})
        assert len(cache._cache) == 3

        # First entry should be evicted
        result = cache.get("q1", "a1")
        assert result is None

    def test_cache_clear(self, cache):
        """Test cache clear removes all entries."""
        cache.set("q1", "a1", {"score": 0.8})
        cache.set("q2", "a2", {"score": 0.9})

        cache.clear()

        assert len(cache._cache) == 0
        assert cache.get("q1", "a1") is None

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        cache.set("q1", "a1", {"score": 0.8})
        cache.set("q2", "a2", {"score": 0.9})

        stats = cache.stats()

        assert stats["size"] == 2
        assert stats["max_size"] == 3
        assert stats["enabled"] is True

    def test_cache_disabled(self):
        """Test cache can be disabled."""
        cache = EvaluationCache()
        cache.enabled = False

        cache.set("query", "answer", {"score": 0.8})
        result = cache.get("query", "answer")

        assert result is None  # Cache disabled, no storage

    def test_singleton_pattern(self):
        """Test get_cache returns singleton."""
        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2


class TestRedisCache:
    """Tests for Redis cache."""

    def test_redis_unavailable(self):
        """Test Redis cache gracefully handles unavailability."""
        from src.eval.cache import RedisCache

        # No Redis URL provided
        cache = RedisCache(redis_url=None)
        assert cache.enabled is False

        # Operations should not fail
        result = cache.get("query", "answer")
        assert result is None

        cache.set("query", "answer", {"score": 0.8})
        # Should not raise error

    def test_redis_stats_disabled(self):
        """Test stats when Redis is disabled."""
        from src.eval.cache import RedisCache

        cache = RedisCache(redis_url=None)
        stats = cache.stats()

        assert stats["enabled"] is False