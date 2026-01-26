#!/usr/bin/env python3
"""
Integration Test Script
Test complete evaluation workflow.

Usage:
    python scripts/eval/test_integration.py
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_database():
    """Test database connection."""
    logger.info("\n1. Testing database connection...")

    from src.eval.database import get_database

    db = get_database()

    if db.health_check():
        logger.info("   ✓ Database connected")
        return True
    else:
        logger.error("   ✗ Database connection failed")
        return False


def test_cache():
    """Test cache functionality."""
    logger.info("\n2. Testing cache...")

    from src.eval.cache import get_cache

    cache = get_cache()

    # Test set/get
    cache.set("test_q", "test_a", {"score": 0.85})
    result = cache.get("test_q", "test_a")

    if result and result.get("score") == 0.85:
        logger.info("   ✓ Cache working")
        return True
    else:
        logger.error("   ✗ Cache test failed")
        return False


def test_trulens():
    """Test TruLens evaluation."""
    logger.info("\n3. Testing TruLens evaluation...")

    from src.eval.trulens import TruLensClient

    client = TruLensClient(enabled=True)

    result = client.evaluate(
        query="What is AI?",
        context="AI is artificial intelligence.",
        answer="AI is a field of computer science.",
    )

    if "record_id" in result and "overall_score" in result:
        logger.info(f"   ✓ TruLens evaluation complete (score: {result['overall_score']:.2f})")
        return True
    else:
        logger.error("   ✗ TruLens evaluation failed")
        return False


def test_guardrails():
    """Test guardrails validation."""
    logger.info("\n4. Testing guardrails...")

    from src.eval.guardrails import InputValidator, OutputValidator, load_guardrails_config

    config = load_guardrails_config()
    input_validator = InputValidator(config)
    output_validator = OutputValidator(config)

    # Test input validation
    passed, _ = input_validator.validate("What is machine learning?")

    if passed:
        logger.info("   ✓ Input validation passed")
    else:
        logger.error("   ✗ Input validation failed")
        return False

    # Test output validation
    passed, _ = output_validator.validate(
        "Machine learning is a subset of AI [1]. It enables systems to learn [2]."
    )

    if passed:
        logger.info("   ✓ Output validation passed")
    else:
        logger.warning("   ⚠ Output validation warnings (expected)")

    return True


def test_performance_tracking():
    """Test performance tracking."""
    logger.info("\n5. Testing performance tracking...")

    from src.eval.performance import PerformanceTracker

    tracker = PerformanceTracker()
    tracker.start()

    with tracker.track("test_operation"):
        time.sleep(0.1)

    tracker.stop()
    metrics = tracker.get_metrics()

    if "test_operation" in metrics and metrics["test_operation"] >= 0.1:
        logger.info(f"   ✓ Performance tracking working ({metrics['test_operation']:.2f}s)")
        return True
    else:
        logger.error("   ✗ Performance tracking failed")
        return False


def test_full_workflow():
    """Test complete evaluation workflow."""
    logger.info("\n6. Testing complete workflow...")

    from src.agents.runner import CrewRunner

    runner = CrewRunner(
        enable_guardrails=True,
        enable_monitoring=True,
    )

    # Disable RAG for faster test
    runner.rag_pipeline = None

    logger.info("   Running crew workflow (this may take 30-60s)...")
    start = time.time()

    result = runner.run(
        topic="What is artificial intelligence?",
        language="en",
    )

    elapsed = time.time() - start

    # Check result
    if not result.evaluation:
        logger.error("   ✗ No evaluation in result")
        return False

    if "performance" not in result.evaluation:
        logger.error("   ✗ No performance metrics")
        return False

    if "trulens" not in result.evaluation:
        logger.error("   ✗ No TruLens metrics")
        return False

    if "guardrails" not in result.evaluation:
        logger.error("   ✗ No guardrails results")
        return False

    logger.info(f"   ✓ Complete workflow successful ({elapsed:.1f}s)")
    logger.info(f"     - TruLens score: {result.evaluation['trulens'].get('overall_score', 0):.2f}")
    logger.info(f"     - Guardrails: {result.evaluation['guardrails'].get('input_passed')}")
    logger.info(f"     - Total time: {result.evaluation['performance'].get('total_time', 0):.2f}s")

    return True


def main():
    """Run all integration tests."""
    logger.info("=" * 70)
    logger.info("EVALUATION INTEGRATION TESTS")
    logger.info("=" * 70)

    tests = [
        ("Database", test_database),
        ("Cache", test_cache),
        ("TruLens", test_trulens),
        ("Guardrails", test_guardrails),
        ("Performance Tracking", test_performance_tracking),
        ("Full Workflow", test_full_workflow),
    ]

    results = []

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"\n   ✗ {name} test failed with exception: {e}")
            results.append((name, False))

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"  {status}: {name}")

    logger.info("\n" + "=" * 70)
    logger.info(f"RESULT: {passed}/{total} tests passed")
    logger.info("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())