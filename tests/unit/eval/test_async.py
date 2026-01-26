"""Tests for async evaluation support."""
from __future__ import annotations

import asyncio

import pytest


class TestAsyncEvaluation:
    """Tests for async evaluation methods."""

    @pytest.mark.asyncio
    async def test_async_evaluate(self):
        """Test async evaluation method."""
        from src.eval.trulens import TruLensClient

        client = TruLensClient(enabled=True)

        result = await client.evaluate_async(
            query="What is AI?",
            context="AI is artificial intelligence.",
            answer="AI is a field of computer science.",
        )

        assert "record_id" in result
        assert "overall_score" in result

    @pytest.mark.asyncio
    async def test_async_multiple_evaluations(self):
        """Test multiple concurrent evaluations."""
        from src.eval.trulens import TruLensClient

        client = TruLensClient(enabled=True)

        # Run 3 evaluations concurrently
        tasks = [
            client.evaluate_async(
                query=f"Query {i}",
                context=f"Context {i}",
                answer=f"Answer {i}",
            )
            for i in range(3)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        for result in results:
            assert "record_id" in result
            assert "overall_score" in result

    @pytest.mark.asyncio
    async def test_async_with_cache(self):
        """Test async evaluation uses cache."""
        from src.eval.trulens import TruLensClient

        client = TruLensClient(enabled=True)

        # First call - cache miss
        result1 = await client.evaluate_async(
            query="What is ML?",
            context="ML is machine learning.",
            answer="ML is a subset of AI.",
        )

        # Second call - should use cache
        result2 = await client.evaluate_async(
            query="What is ML?",
            context="ML is machine learning.",
            answer="ML is a subset of AI.",
        )

        # Results should be identical (from cache)
        assert result1["record_id"] == result2["record_id"]