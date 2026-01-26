#!/usr/bin/env python3
"""
Export Evaluation Metrics
Export evaluation metrics to CSV or JSON.

Usage:
    python scripts/eval/export_metrics.py --output metrics.csv
    python scripts/eval/export_metrics.py --output metrics.json --format json
    python scripts/eval/export_metrics.py --limit 100
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.eval.database import get_database
from src.eval.models import EvaluationRecord, PerformanceMetrics, QualityMetrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def export_csv(records: list[dict], output_path: Path):
    """Export records to CSV."""
    if not records:
        logger.warning("No records to export")
        return

    fieldnames = list(records[0].keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Exported {len(records)} records to {output_path}")


def export_json(records: list[dict], output_path: Path):
    """Export records to JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)

    logger.info(f"Exported {len(records)} records to {output_path}")


def main():
    """Export metrics."""
    parser = argparse.ArgumentParser(description="Export evaluation metrics")
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output file path",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["csv", "json"],
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum records to export (default: 1000)",
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("EXPORT EVALUATION METRICS")
    logger.info("=" * 70)

    # Connect to database
    db = get_database()

    if not db.health_check():
        logger.error("Database not available!")
        return 1

    # Query records
    logger.info(f"Fetching up to {args.limit} records...")

    with db.get_session() as session:
        results = (
            session.query(EvaluationRecord, PerformanceMetrics, QualityMetrics)
            .outerjoin(
                PerformanceMetrics,
                EvaluationRecord.record_id == PerformanceMetrics.record_id,
            )
            .outerjoin(
                QualityMetrics,
                EvaluationRecord.record_id == QualityMetrics.record_id,
            )
            .order_by(EvaluationRecord.ts.desc())
            .limit(args.limit)
            .all()
        )

    logger.info(f"Found {len(results)} records")

    # Convert to dictionaries
    records = []
    for eval_record, perf, quality in results:
        record = {
            "record_id": eval_record.record_id,
            "timestamp": eval_record.ts,
            "app_id": eval_record.app_id,
            "query": eval_record.input,
            "answer_length": len(eval_record.output),
            # Performance
            "total_time": perf.total_time if perf else None,
            "rag_time": perf.rag_retrieval_time if perf else None,
            "llm_time": perf.llm_inference_time if perf else None,
            # Quality
            "rouge_1": quality.rouge_1 if quality else None,
            "rouge_2": quality.rouge_2 if quality else None,
            "bleu": quality.bleu_score if quality else None,
            "factuality": quality.factuality_score if quality else None,
        }
        records.append(record)

    # Export
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "csv":
        export_csv(records, output_path)
    else:
        export_json(records, output_path)

    logger.info("=" * 70)
    logger.info("EXPORT COMPLETE")
    logger.info("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())