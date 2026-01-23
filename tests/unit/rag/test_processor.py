"""Unit tests for document processor."""
import pytest
from src.rag.ingestion.processor import DocumentProcessor
from haystack.dataclasses import Document

def test_chunk_id_deterministic():
    """Test that chunk IDs are deterministic."""
    processor = DocumentProcessor()
    
    # Same content should produce same ID
    id1 = processor._generate_chunk_id("source.txt", "test content", 0)
    id2 = processor._generate_chunk_id("source.txt", "test content", 0)
    
    assert id1 == id2

def test_chunk_id_unique_for_different_content():
    """Test that different content produces different IDs."""
    processor = DocumentProcessor()
    
    id1 = processor._generate_chunk_id("source.txt", "content 1", 0)
    id2 = processor._generate_chunk_id("source.txt", "content 2", 0)
    
    assert id1 != id2

def test_process_documents_creates_correct_metadata():
    """Test that processed chunks have correct metadata."""
    processor = DocumentProcessor()
    
    docs = [
        Document(
            content="Test content",
            meta={"source": "test.txt", "_split_id": 0}
        )
    ]
    
    processed = processor.process_documents(docs)
    
    assert len(processed) == 1
    assert processed[0].properties["source"] == "test.txt"
    assert processed[0].properties["chunk_index"] == 0
    assert "chunk_hash" in processed[0].properties