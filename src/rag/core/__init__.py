"""
RAG Core Module.

Core infrastructure for retrieval-augmented generation.
Provides the main pipeline, schema management, and service layer.
"""
from __future__ import annotations

from .pipeline import RAGPipeline
from .schema import SCHEMA_VERSION, SchemaManager, SchemaValidationError
from .service import RAGService

__all__ = [
    "RAGPipeline",
    "RAGService",
    "SchemaManager",
    "SchemaValidationError",
    "SCHEMA_VERSION",
]