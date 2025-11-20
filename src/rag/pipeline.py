from __future__ import annotations

from dataclasses import dataclass
from typing import List

from haystack.dataclasses import Document


@dataclass
class RAGPipeline:
    """
    Placeholder for our full Haystack RAG pipeline.

    In a later phase this will:
    - load / index documents into a vector store (e.g. Weaviate),
    - run retrieval,
    - format context for the multi-agent system.
    """

    def run(self, query: str, top_k: int = 5) -> List[Document]:
        # Phase-0: only a stub, not wired anywhere
        raise NotImplementedError(
            "RAGPipeline is not implemented yet. Use RAGService.generate_summary instead."
        )
