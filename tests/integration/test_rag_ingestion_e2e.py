"""End-to-end test for RAG ingestion workflow."""
import pytest
import os
from pathlib import Path
from src.rag.ingestion import IngestionEngine
from src.rag.sources import LocalFileSource

@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS", "").lower() in {"1", "true"},
    reason="Integration tests skipped"
)
def test_full_ingestion_workflow(tmp_path):
    """Test complete ingestion workflow from file to Weaviate."""
    # 1. Create test document
    test_file = tmp_path / "test.txt"
    test_file.write_text(
        "Artificial intelligence is a field of computer science. "
        "Machine learning is a subset of AI."
    )
    
    # 2. Initialize engine
    engine = IngestionEngine()
    engine.clear_index()
    
    # 3. Ingest from local source
    source = LocalFileSource(tmp_path)
    result = engine.ingest_from_source(source)
    
    # 4. Verify ingestion
    assert result.documents_loaded > 0
    assert result.chunks_ingested > 0
    assert result.chunks_skipped == 0
    
    # 5. Re-ingest (should skip duplicates)
    result2 = engine.ingest_from_source(source)
    assert result2.chunks_skipped == result.chunks_ingested
    assert result2.chunks_ingested == 0
    
    # Cleanup
    engine.client.close()