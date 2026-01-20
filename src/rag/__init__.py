"""
Retrieval-Augmented Generation (RAG) Module

Main exports for RAG functionality.
"""
from __future__ import annotations

from .core import RAGPipeline, RAGService, SchemaManager
from .ingestion import IngestionEngine
from .sources import ArXivSource, DocumentSource, LocalFileSource

__all__ = [
    "RAGPipeline",
    "RAGService",
    "SchemaManager",
    "IngestionEngine",
    "DocumentSource",
    "LocalFileSource",
    "ArXivSource",
]