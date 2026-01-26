"""
Quality Metrics Storage
Store ROUGE/BLEU metrics to database.
"""
from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def store_quality_metrics(
    record_id: str,
    rouge_scores: dict,
    bleu_score: float,
    semantic_similarity: float,
    factuality_score: float,
    factuality_issues: list[str],
    citation_count: int,
    answer: str,
):
    """
    Store quality metrics to database.
    
    Args:
        record_id: Evaluation record ID
        rouge_scores: ROUGE scores dictionary
        bleu_score: BLEU score
        semantic_similarity: Semantic similarity score
        factuality_score: Factuality score
        factuality_issues: List of factuality issues
        citation_count: Number of citations
        answer: Full answer text
    """
    try:
        from ..database import get_database
        from ..models import QualityMetrics

        db = get_database()

        # Calculate sentence count
        sentence_count = len([s for s in answer.split(".") if s.strip()])

        quality_data = QualityMetrics(
            record_id=record_id,
            timestamp=datetime.utcnow(),
            rouge_1=rouge_scores.get("rouge-1"),
            rouge_2=rouge_scores.get("rouge-2"),
            rouge_l=rouge_scores.get("rouge-l"),
            bleu_score=bleu_score,
            semantic_similarity=semantic_similarity,
            factuality_score=factuality_score,
            factuality_issues=factuality_issues,
            citation_count=citation_count,
            answer_length=len(answer),
            sentence_count=sentence_count,
        )

        with db.get_session() as session:
            session.add(quality_data)
            session.commit()

        logger.info("Stored quality metrics for record %s", record_id)

    except Exception as e:
        logger.error("Failed to store quality metrics: %s", e)