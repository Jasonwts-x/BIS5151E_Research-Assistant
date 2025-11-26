from __future__ import annotations

from src.rag.pipeline import RAGPipeline
from src.rag.service import RAGService


def test_rag_pipeline_builds_and_retrieves() -> None:
    """
    Smoke test: RAGPipeline.from_config() should build an index
    and return a list of documents for a simple query.
    """
    pipeline = RAGPipeline.from_config()
    docs = pipeline.run(query="generative AI", top_k=3)
    assert isinstance(docs, list)
    # We don't assert on length to avoid flakiness if data set changes.


def test_build_context_from_empty_docs() -> None:
    """
    RAGService.build_context_from_docs([]) should produce a friendly fallback.
    """
    text = RAGService.build_context_from_docs([])
    assert "No external context was retrieved" in text
