from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from haystack.dataclasses import Document

from ..agents.orchestrator import (
    Orchestrator,
    PipelineResult,
    default_orchestrator,
)
from ..utils.config import AppConfig, load_config
from .pipeline import RAGPipeline

logger = logging.getLogger(__name__)


@dataclass
class RAGService:
    """
    High-level RAG + multi-agent facade.

    Responsibilities:
    - Build / hold a RAGPipeline (BM25 over data/raw).
    - Retrieve relevant chunks for a topic.
    - Format context for the multi-agent orchestrator.
    - Run Writer → Reviewer → FactChecker → (optional) Translator.
    """

    config: Optional[AppConfig] = None
    pipeline: Optional[RAGPipeline] = None
    orchestrator: Optional[Orchestrator] = None

    def __post_init__(self) -> None:
        if self.config is None:
            self.config = load_config()

        if self.pipeline is None:
            try:
                self.pipeline = RAGPipeline.from_config()
            except Exception as exc:
                logger.warning(
                    "RAGService: could not build RAGPipeline (%s). "
                    "RAG-based context will be unavailable until fixed.",
                    exc,
                )
                self.pipeline = None

        if self.orchestrator is None:
            self.orchestrator = default_orchestrator()

    # ------------------------------------------------------------------ #
    # RAG helpers
    # ------------------------------------------------------------------ #
    def retrieve_documents(self, topic: str) -> List[Document]:
        """
        Retrieve top-k chunks for the topic via the RAG pipeline.
        If the pipeline is not available, returns an empty list.
        """
        if self.pipeline is None:
            logger.warning(
                "RAGService: pipeline is None, returning empty document list."
            )
            return []

        top_k = self.config.rag.top_k
        return self.pipeline.run(query=topic, top_k=top_k)

    @staticmethod
    def build_context_from_docs(docs: List[Document]) -> str:
        """
        Turn retrieved Haystack Documents into a text context string.

        We number sources like [1], [2] based on their 'source' metadata so
        that agents can later produce consistent inline citations.
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
    # Multi-agent orchestration entry point
    # ------------------------------------------------------------------ #
    def run_with_agents(
        self,
        topic: str,
        language: str = "en",
    ) -> PipelineResult:
        """
        Run the full pipeline:
        - RAG retrieval for the topic
        - Multi-agent orchestration (Writer → Reviewer → FactChecker → Translator)
        """
        if self.orchestrator is None:
            raise RuntimeError("RAGService.orchestrator is not initialized.")

        docs = self.retrieve_documents(topic)
        context = self.build_context_from_docs(docs)

        logger.info(
            "RAGService: running orchestrator for topic='%s', language='%s'",
            topic,
            language,
        )

        return self.orchestrator.run_pipeline(
            topic=topic,
            language=language,
            context=context,
        )

    # ------------------------------------------------------------------ #
    # Compatibility helper
    # ------------------------------------------------------------------ #
    def generate_summary(
        self,
        topic: str,
        max_sentences: int | None = 8,
        language: str = "en",
    ) -> str:
        """
        Backwards-compatible entry:

        - Previously: single LLM call via local_llm_query.
        - Now: RAG + multi-agent pipeline; returns only the *final* text.

        `max_sentences` is kept for compatibility (agents already constrain
        length in their prompts, so this is currently not enforced).
        """
        result = self.run_with_agents(topic=topic, language=language)
        return result.final_output
