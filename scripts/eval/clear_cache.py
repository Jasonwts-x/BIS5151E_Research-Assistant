#!/usr/bin/env python3
"""
Clear Evaluation Cache
Clear in-memory or Redis evaluation cache.

Usage:
    python scripts/eval/clear_cache.py
    python scripts/eval/clear_cache.py --redis
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.eval.cache import get_cache, get_redis_cache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Clear cache."""
    parser = argparse.ArgumentParser(description="Clear evaluation cache")
    parser.add_argument(
        "--redis",
        action="store_true",
        help="Clear Redis cache instead of in-memory cache",
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("CLEAR EVALUATION CACHE")
    logger.info("=" * 70)

    if args.redis:
        logger.info("Clearing Redis cache...")
        cache = get_redis_cache()

        if not cache.enabled:
            logger.error("Redis cache is not enabled!")
            logger.info("Set REDIS_URL environment variable to enable Redis")
            return 1

        # Get stats before clearing
        stats_before = cache.stats()
        logger.info(f"Cache stats before: {stats_before}")

        # Clear
        cache.clear()

        # Get stats after
        stats_after = cache.stats()
        logger.info(f"Cache stats after: {stats_after}")

        logger.info("✓ Redis cache cleared")

    else:
        logger.info("Clearing in-memory cache...")
        cache = get_cache()

        # Get stats before clearing
        stats_before = cache.stats()
        logger.info(f"Cache stats before: {stats_before}")

        # Clear
        cache.clear()

        # Get stats after
        stats_after = cache.stats()
        logger.info(f"Cache stats after: {stats_after}")

        logger.info("✓ In-memory cache cleared")

    logger.info("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())