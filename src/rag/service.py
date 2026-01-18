from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from haystack.dataclasses import Document

from ..utils.config import AppConfig, load_config
from .pipeline import RAGPipeline

logger = logging.getLogger(__name__)


@dataclass
class RAGService:
    """
    RAG service focused on document retrieval and context formatting.

    Responsibilities:
    - Build / hold a RAGPipeline (Weaviate + hybrid retrieval).
    - Retrieve relevant chunks for a topic.
    - Format context with proper citations for downstream agents.

    Note: Multi-agent orchestration is now handled by the separate CrewAI service.
    This service is purely for retrieval.
    """

    config: Optional[AppConfig] = None
    pipeline: Optional[RAGPipeline] = None

    def __post_init__(self) -> None:
        if self.config is None:
            self.config = load_config()

        if self.pipeline is None:
            try:
                self.pipeline = RAGPipeline.from_config()
                logger.info("RAGService: RAGPipeline initialized successfully")
            except Exception as exc:
                logger.warning(
                    "RAGService: could not build RAGPipeline (%s). "
                    "RAG-based context will be unavailable until fixed.",
                    exc,
                )
                self.pipeline = None

    # ------------------------------------------------------------------ #
    # RAG retrieval
    # ------------------------------------------------------------------ #
    def retrieve_documents(self, topic: str, top_k: Optional[int] = None) -> List[Document]:
        """
        Retrieve top-k chunks for the topic via the RAG pipeline.
        If the pipeline is not available, returns an empty list.
        
        Args:
            topic: Search query / research topic
            top_k: Number of documents to retrieve (uses config default if not specified)
        """
        if self.pipeline is None:
            logger.warning(
                "RAGService: pipeline is None, returning empty document list."
            )
            return []

        k = top_k if top_k is not None else self.config.rag.top_k
        return self.pipeline.run(query=topic, top_k=k)

    @staticmethod
    def build_context_from_docs(docs: List[Document]) -> str:
        """
        Turn retrieved Haystack Documents into a text context string.

        We number sources like [1], [2] based on their 'source' metadata so
        that agents can later produce consistent inline citations.
        
        Args:
            docs: List of retrieved Haystack Documents
            
        Returns:
            Formatted context string with citations
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

    # ------------------------------------------------------------------ #
    # High-level convenience method
    # ------------------------------------------------------------------ #
    def retrieve_and_format(self, topic: str, top_k: Optional[int] = None) -> tuple[str, List[Document]]:
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