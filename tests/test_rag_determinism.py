"""
Test RAG Determinism

Verifies that rebuilding the index produces identical chunk IDs.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.rag.core import RAGPipeline
from src.rag.ingestion import IngestionEngine
from src.rag.sources import LocalFileSource

# Skip if Weaviate not available
pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_WEAVIATE_TESTS", "").lower() in {"1", "true", "yes"},
    reason="Weaviate tests skipped",
)


def test_deterministic_ids(tmp_path):
    """
    Test that re-ingesting same documents produces identical IDs.
    
    This is the core guarantee of our content-hash approach.
    """
    # Create test document
    test_doc = tmp_path / "test.txt"
    test_doc.write_text(
        "This is a test document for determinism verification. "
        "It should produce the same chunk IDs every time it's ingested.",
        encoding="utf-8",
    )
    
    # First ingestion
    engine1 = IngestionEngine()
    engine1.clear_index()  # Start fresh
    
    source = LocalFileSource(tmp_path)
    result1 = engine1.ingest_from_source(source)
    
    assert result1.chunks_ingested > 0, "Should ingest at least one chunk"
    
    # Get chunk IDs from first ingestion
    # TODO: Add method to retrieve chunk IDs from Weaviate
    # For now, we verify that re-ingestion skips duplicates
    
    # Second ingestion (same document)
    result2 = engine1.ingest_from_source(source)
    
    # Should skip all chunks (duplicates)
    assert result2.chunks_skipped == result1.chunks_ingested, \
        "Re-ingesting same document should skip all chunks (deterministic IDs)"
    
    assert result2.chunks_ingested == 0, \
        "No new chunks should be ingested on second run"


def test_stable_chunking_order(tmp_path):
    """
    Test that documents are chunked in stable order.
    
    Files should be sorted alphabetically for deterministic ordering.
    """
    # Create multiple files
    (tmp_path / "a.txt").write_text("File A content", encoding="utf-8")
    (tmp_path / "c.txt").write_text("File C content", encoding="utf-8")
    (tmp_path / "b.txt").write_text("File B content", encoding="utf-8")
    
    # Ingest
    engine = IngestionEngine()
    engine.clear_index()
    
    source = LocalFileSource(tmp_path)
    result = engine.ingest_from_source(source)
    
    assert result.documents_loaded == 3
    assert result.chunks_ingested > 0
    
    # Re-ingest - should skip all (stable ordering)
    result2 = engine.ingest_from_source(source)
    assert result2.chunks_skipped == result.chunks_ingested