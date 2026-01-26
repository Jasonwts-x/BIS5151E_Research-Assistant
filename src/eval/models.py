"""
SQLAlchemy Models for Evaluation Database
Defines database tables for storing evaluation metrics.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class EvaluationRecord(Base):
    """Main evaluation record (compatible with TruLens records table)."""

    __tablename__ = "records"

    record_id = Column(String(255), primary_key=True)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    app_id = Column(String(255), nullable=False)
    input = Column(Text, nullable=False)  # Query
    output = Column(Text, nullable=False)  # Answer
    tags = Column(String(255))

    # Relationships
    performance = relationship(
        "PerformanceMetrics", back_populates="record", cascade="all, delete-orphan"
    )
    quality = relationship(
        "QualityMetrics", back_populates="record", cascade="all, delete-orphan"
    )
    guardrails = relationship(
        "GuardrailsResults", back_populates="record", cascade="all, delete-orphan"
    )


class PerformanceMetrics(Base):
    """Performance timing metrics."""

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(255), ForeignKey("records.record_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Timing breakdown
    total_time = Column(Float)
    rag_retrieval_time = Column(Float)
    agent_writer_time = Column(Float)
    agent_reviewer_time = Column(Float)
    agent_factchecker_time = Column(Float)
    llm_inference_time = Column(Float)
    guardrails_time = Column(Float)
    evaluation_time = Column(Float)

    # Resource metrics
    memory_usage_mb = Column(Float)
    token_count = Column(Integer)

    # Metadata
    model_name = Column(String(100))
    language = Column(String(10))

    # Relationship
    record = relationship("EvaluationRecord", back_populates="performance")


class QualityMetrics(Base):
    """Quality assessment metrics (ROUGE, BLEU, etc.)."""

    __tablename__ = "quality_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(255), ForeignKey("records.record_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # ROUGE scores
    rouge_1 = Column(Float)
    rouge_2 = Column(Float)
    rouge_l = Column(Float)

    # BLEU score
    bleu_score = Column(Float)

    # Semantic similarity
    semantic_similarity = Column(Float)

    # Factuality
    factuality_score = Column(Float)
    factuality_issues = Column(ARRAY(Text))

    # Citation metrics
    citation_count = Column(Integer)
    citation_quality = Column(Float)

    # Answer metrics
    answer_length = Column(Integer)
    sentence_count = Column(Integer)

    # Consistency metrics
    consistency_runs = Column(Integer)          # Number of runs for consistency check
    consistency_std_dev = Column(Float)         # Standard deviation of scores
    consistency_passed = Column(Boolean)        # Whether consistency check passed

    # Paraphrase stability metrics
    paraphrase_variations = Column(Integer)     # Number of variations tested
    paraphrase_max_diff = Column(Float)         # Maximum score difference
    paraphrase_stable = Column(Boolean)         # Whether paraphrase check passed

    # Relationship
    record = relationship("EvaluationRecord", back_populates="quality")


class GuardrailsResults(Base):
    """Guardrails validation results."""

    __tablename__ = "guardrails_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(255), ForeignKey("records.record_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Overall validation
    input_passed = Column(Boolean, nullable=False)
    output_passed = Column(Boolean, nullable=False)
    overall_passed = Column(Boolean, nullable=False)

    # Input validation details
    jailbreak_detected = Column(Boolean, default=False)
    pii_detected = Column(Boolean, default=False)
    off_topic_detected = Column(Boolean, default=False)

    # Output validation details
    citation_issues = Column(Boolean, default=False)
    hallucination_markers = Column(Boolean, default=False)
    length_violation = Column(Boolean, default=False)
    harmful_content = Column(Boolean, default=False)

    # Violation details
    violations = Column(ARRAY(Text))
    warnings = Column(ARRAY(Text))

    # Relationship
    record = relationship("EvaluationRecord", back_populates="guardrails")