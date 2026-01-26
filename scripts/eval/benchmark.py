#!/usr/bin/env python3
"""
Evaluation Benchmarking Script
Run comprehensive benchmarks on the evaluation system.

Usage:
    python scripts/eval/benchmark.py
    python scripts/eval/benchmark.py --queries 5 --runs 3
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.agents.runner import CrewRunner
from src.eval.quality import ConsistencyCalculator, ParaphraseStabilityCalculator
from src.eval.trulens import FeedbackProvider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def benchmark_consistency(query: str, context: str, runs: int = 3):
    """
    Benchmark consistency across multiple runs.
    
    Args:
        query: Test query
        context: Context for query
        runs: Number of runs to test
    """
    logger.info("Running consistency benchmark...")
    logger.info(f"  Query: {query}")
    logger.info(f"  Runs: {runs}")

    runner = CrewRunner(enable_guardrails=True, enable_monitoring=True)
    scores = []

    for i in range(runs):
        logger.info(f"  Run {i+1}/{runs}...")
        result = runner.run(topic=query, language="en")

        if result.evaluation and "trulens" in result.evaluation:
            score = result.evaluation["trulens"].get("overall_score", 0)
            scores.append(score)
            logger.info(f"    Score: {score:.3f}")

    # Calculate consistency
    calculator = ConsistencyCalculator()
    consistency = calculator.calculate(scores)

    logger.info("\nConsistency Results:")
    logger.info(f"  Mean: {consistency['mean']:.3f}")
    logger.info(f"  Std Dev: {consistency['std_dev']:.3f}")
    logger.info(f"  Consistent: {consistency['consistent']}")
    logger.info(f"  Threshold: {consistency['threshold']}")

    return consistency


def benchmark_paraphrase(
    query_variations: list[str],
    context: str,
    answer: str,
):
    """
    Benchmark paraphrase stability.
    
    Args:
        query_variations: List of paraphrased queries
        context: Context for all queries
        answer: Answer to evaluate
    """
    logger.info("Running paraphrase stability benchmark...")
    logger.info(f"  Variations: {len(query_variations)}")

    provider = FeedbackProvider()

    def evaluator(query, context, answer):
        score, _ = provider.groundedness_score(context, answer)
        return score

    calculator = ParaphraseStabilityCalculator(evaluator)
    stability = calculator.calculate(query_variations, context, answer)

    logger.info("\nParaphrase Stability Results:")
    logger.info(f"  Max Difference: {stability['max_diff']:.3f}")
    logger.info(f"  Mean Score: {stability['mean_score']:.3f}")
    logger.info(f"  Stable: {stability['stable']}")
    logger.info(f"  Threshold: {stability['threshold']}")

    return stability


def benchmark_performance(queries: list[str], runs: int = 3):
    """
    Benchmark performance across multiple queries.
    
    Args:
        queries: List of test queries
        runs: Runs per query
    """
    logger.info("Running performance benchmark...")
    logger.info(f"  Queries: {len(queries)}")
    logger.info(f"  Runs per query: {runs}")

    runner = CrewRunner(enable_guardrails=True, enable_monitoring=True)
    results = []

    for query in queries:
        logger.info(f"\n  Query: {query}")
        query_times = []

        for i in range(runs):
            start = time.time()
            result = runner.run(topic=query, language="en")
            end = time.time()

            elapsed = end - start
            query_times.append(elapsed)

            if result.evaluation and "performance" in result.evaluation:
                perf = result.evaluation["performance"]
                logger.info(f"    Run {i+1}: {perf.get('total_time', elapsed):.2f}s")

        avg_time = sum(query_times) / len(query_times)
        results.append(
            {
                "query": query,
                "avg_time": avg_time,
                "min_time": min(query_times),
                "max_time": max(query_times),
                "runs": runs,
            }
        )

    logger.info("\nPerformance Summary:")
    for result in results:
        logger.info(f"  {result['query'][:50]}...")
        logger.info(f"    Avg: {result['avg_time']:.2f}s")
        logger.info(f"    Min: {result['min_time']:.2f}s")
        logger.info(f"    Max: {result['max_time']:.2f}s")

    return results


def main():
    """Run benchmarks."""
    parser = argparse.ArgumentParser(description="Evaluation Benchmarking")
    parser.add_argument(
        "--queries",
        type=int,
        default=3,
        help="Number of queries to test (default: 3)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Runs per query (default: 3)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file for results",
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("EVALUATION BENCHMARKING")
    logger.info("=" * 70)

    # Test queries
    test_queries = [
        "What is retrieval augmented generation?",
        "Explain transformers in deep learning",
        "What are the benefits of RAG systems?",
        "How do vector databases work?",
        "What is semantic search?",
    ][: args.queries]

    # Paraphrase variations
    query_variations = [
        "What is RAG?",
        "Can you explain retrieval augmented generation?",
        "What does RAG mean in AI?",
        "Describe RAG systems",
    ]

    # Sample context and answer
    sample_context = "RAG is a technique that combines retrieval with generation."
    sample_answer = "RAG (Retrieval Augmented Generation) combines information retrieval with text generation [1]."

    # Run benchmarks
    results = {}

    # 1. Consistency benchmark
    try:
        consistency = benchmark_consistency(
            test_queries[0],
            sample_context,
            runs=args.runs,
        )
        results["consistency"] = consistency
    except Exception as e:
        logger.error(f"Consistency benchmark failed: {e}")

    # 2. Paraphrase stability benchmark
    try:
        stability = benchmark_paraphrase(
            query_variations,
            sample_context,
            sample_answer,
        )
        results["paraphrase_stability"] = stability
    except Exception as e:
        logger.error(f"Paraphrase benchmark failed: {e}")

    # 3. Performance benchmark
    try:
        performance = benchmark_performance(test_queries, runs=args.runs)
        results["performance"] = performance
    except Exception as e:
        logger.error(f"Performance benchmark failed: {e}")

    # Save results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"\nResults saved to: {output_path}")

    logger.info("\n" + "=" * 70)
    logger.info("BENCHMARKING COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()