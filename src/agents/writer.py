from __future__ import annotations

from dataclasses import dataclass

from ..rag.service import RAGService


@dataclass
class WriterAgent:
    """
    Drafts an initial summary using the RAG service (or plain LLM in Phase-0).
    """

    rag: RAGService

    def draft(self, topic: str) -> str:
        return self.rag.generate_summary(topic)
