"""
Document Ingestion Module

Handles document processing and ingestion into Weaviate.
"""
from __future__ import annotations

from .engine import IngestionEngine, IngestionResult
from .processor import DocumentProcessor, ProcessedChunk

__all__ = [
    "IngestionEngine",
    "IngestionResult",
    "DocumentProcessor",
    "ProcessedChunk",
]