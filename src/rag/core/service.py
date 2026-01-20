"""
RAG Service - Simplified

Focuses on retrieval and context formatting.
Ingestion is now handled by IngestionEngine.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from haystack.dataclasses import Document

from ...utils.config import AppConfig, load_config
from .pipeline import RAGPipeline

logger = logging.getLogger(__name__)


@dataclass
class RAGService:
    """
    RAG service for retrieval and context formatting.
    
    Responsibilities:
    - Retrieve documents via RAGPipeline
    - Format context with citations
    
    Note: Ingestion is handled by IngestionEngine (separate concern)
    """

    config: Optional[AppConfig] = None
    pipeline: Optional[RAGPipeline] = None

    def __post_init__(self) -> None:
        if self.config is None:
            self.config = load_config()

        if self.pipeline is None:
            try:
                self.pipeline = RAGPipeline.from_existing()
                logger.info("RAGService: RAGPipeline initialized successfully")
            except Exception as exc:
                logger.warning(
                    "RAGService: could not connect to RAG pipeline (%s). "
                    "Index may be empty or Weaviate not ready.",
                    exc,
                )
                self.pipeline = None

    def retrieve_documents(
        self,
        topic: str,
        top_k: Optional[int] = None,
    ) -> List[Document]:
        """
        Retrieve top-k chunks for the topic.
        
        Args:
            topic: Search query / research topic
            top_k: Number of documents to retrieve (uses config default if not specified)
            
        Returns:
            List of relevant documents
        """
        if self.pipeline is None:
            logger.warning("RAGService: pipeline is None, returning empty list")
            return []

        k = top_k if top_k is not None else self.config.rag.top_k
        return self.pipeline.run(query=topic, top_k=k)

    @staticmethod
    def build_context_from_docs(docs: List[Document]) -> str:
        """
        Format retrieved documents into context string with citations.
        
        Args:
            docs: List of retrieved Haystack Documents
            
        Returns:
            Formatted context string with [1], [2], ... citations
        """
        if not docs:
            return "No external context was retrieved.\n"

        unique_sources: list[str] = []
        lines: list[str] = []

        for d in docs:
            meta = getattr(d, "meta", {}) or {}
            src = meta.get("source", "unknown")
            if src not in unique_sources:
                unique_sources.append(src)
            idx = unique_sources.index(src) + 1
            lines.append(f"[{idx}] {d.content.strip()}")

        context = "\n\n".join(lines)
        source_map = "\n".join(f"[{i+1}] {s}" for i, s in enumerate(unique_sources))
        return f"{context}\n\nSources:\n{source_map}"

    def retrieve_and_format(
        self,
        topic: str,
        top_k: Optional[int] = None,
    ) -> tuple[str, List[Document]]:
        """
        Convenience method: retrieve documents and format context in one call.
        
        Args:
            topic: Search query / research topic
            top_k: Number of documents to retrieve (optional)
            
        Returns:
            Tuple of (formatted_context_string, list_of_documents)
        """
        docs = self.retrieve_documents(topic, top_k)
        context = self.build_context_from_docs(docs)
        return context, docs