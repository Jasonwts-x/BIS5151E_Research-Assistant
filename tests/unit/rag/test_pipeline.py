"""Unit tests for RAG pipeline."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestRAGPipeline:
    """Tests for RAGPipeline."""

    def test_from_existing_raises_if_collection_missing(self):
        """Test from_existing raises error if collection doesn't exist."""
        with patch("src.rag.core.pipeline.load_config"):
            with patch("src.rag.core.pipeline.RAGPipeline._create_weaviate_client") as mock_create:
                mock_client = MagicMock()
                mock_client.collections.exists.return_value = False
                mock_create.return_value = mock_client
                
                from src.rag.core.pipeline import RAGPipeline
                
                with pytest.raises(RuntimeError, match="Collection .* does not exist"):
                    RAGPipeline.from_existing()
                
                # Should close client on error
                mock_client.close.assert_called_once()

    def test_pipeline_context_manager(self):
        """Test pipeline can be used as context manager."""
        with patch("src.rag.core.pipeline.load_config"):
            with patch("src.rag.core.pipeline.RAGPipeline._create_weaviate_client"):
                with patch("src.rag.core.pipeline.RAGPipeline.from_existing") as mock_from:
                    mock_pipeline = MagicMock()
                    mock_from.return_value = mock_pipeline
                    
                    # Use as context manager
                    with mock_pipeline as pipeline:
                        pass
                    
                    # Should call close
                    mock_pipeline.close.assert_called_once()

    def test_close_handles_none_client(self):
        """Test close handles None client gracefully."""
        from src.rag.core.pipeline import RAGPipeline
        
        pipeline = RAGPipeline(
            client=None,
            retriever=None,
            text_embedder=None,
            collection_name="test"
        )
        
        # Should not raise
        pipeline.close()