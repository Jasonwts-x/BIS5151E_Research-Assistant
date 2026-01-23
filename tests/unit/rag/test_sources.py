"""Unit tests for document sources."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from haystack.dataclasses import Document

from src.rag.sources.local import LocalFileSource


class TestLocalFileSource:
    """Tests for LocalFileSource."""

    def test_fetch_returns_documents(self, tmp_path):
        """Test fetch returns list of documents."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        source = LocalFileSource(tmp_path)
        docs = source.fetch(pattern="*")
        
        assert isinstance(docs, list)
        assert len(docs) > 0
        assert all(isinstance(d, Document) for d in docs)

    def test_fetch_skips_missing_files(self, tmp_path):
        """Test fetch handles missing files gracefully."""
        source = LocalFileSource(tmp_path)
        docs = source.fetch(pattern="nonexistent*")
        
        assert docs == []

    def test_fetch_with_pattern(self, tmp_path):
        """Test fetch respects file pattern."""
        (tmp_path / "arxiv-123.pdf").write_bytes(b"%PDF-1.4\ntest")
        (tmp_path / "other.txt").write_text("other")
        
        source = LocalFileSource(tmp_path)
        
        with patch("src.rag.sources.local.PyPDFToDocument") as mock_pdf:
            mock_pdf.return_value.run.return_value = {
                "documents": [Document(content="PDF content")]
            }
            
            docs = source.fetch(pattern="arxiv*")
            
            # Should only process matching file
            assert len(docs) == 1

    def test_get_source_name(self, tmp_path):
        """Test source name includes directory."""
        source = LocalFileSource(tmp_path)
        name = source.get_source_name()
        
        assert "LocalFiles" in name
        assert str(tmp_path) in name


class TestArXivSource:
    """Tests for ArXivSource."""

    def test_fetch_calls_arxiv_api(self):
        """Test fetch calls ArXiv API."""
        from src.rag.sources.arxiv import ArXivSource
        
        with patch("src.rag.sources.arxiv.arxiv.Search") as mock_search:
            mock_result = MagicMock()
            mock_result.get_short_id.return_value = "2401.12345"
            mock_result.title = "Test Paper"
            mock_result.pdf_url = "http://example.com/paper.pdf"
            mock_result.authors = []
            mock_result.published = None
            mock_result.summary = "Test abstract"
            mock_result.primary_category = "cs.AI"
            
            mock_search.return_value.results.return_value = [mock_result]
            
            source = ArXivSource()
            
            with patch.object(source, "_download_pdf") as mock_download:
                with patch.object(source, "_pdf_to_document") as mock_convert:
                    mock_convert.return_value = Document(content="test")
                    
                    docs = source.fetch(query="test", max_results=1)
                    
                    assert len(docs) == 1
                    mock_download.assert_called_once()

    def test_slugify(self):
        """Test title slugification."""
        from src.rag.sources.arxiv import ArXivSource
        
        slug = ArXivSource._slugify("This is: A Test! Title?")
        
        assert slug == "this-is-a-test-title"
        assert len(slug) <= 60