"""
Retrieval-Augmented Generation (RAG) Module.

This module implements the complete RAG pipeline for the Research Assistant project,
integrating document ingestion, embedding generation, vector storage, and retrieval.

Architecture:
    - Core: RAG pipeline, schema management, and service layer
    - Ingestion: Document processing and Weaviate integration
    - Sources: Abstraction for loading documents from multiple sources

Main Components:
    RAGPipeline: Hybrid retrieval engine (BM25 + semantic search)
    RAGService: High-level service for retrieval and context formatting
    SchemaManager: Weaviate schema lifecycle management
    IngestionEngine: Orchestrates document → chunks → embeddings → storage
    DocumentSource: Abstract base for data source implementations
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