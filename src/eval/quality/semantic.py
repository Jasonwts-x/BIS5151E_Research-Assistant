"""
Semantic Similarity Calculator
Measures semantic similarity using embeddings.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SemanticSimilarityCalculator:
    """
    Calculate semantic similarity using sentence embeddings.
    
    Uses the same embedding model as RAG pipeline for consistency.
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize calculator.
        
        Args:
            model_name: Embedding model name (defaults to RAG config)
        """
        if model_name is None:
            from ...utils.config import load_config
            config = load_config()
            model_name = config.weaviate.embedding_model

        self.model_name = model_name
        self._model = None
        logger.info("SemanticSimilarityCalculator initialized with model: %s", model_name)

    def _load_model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info("Loaded embedding model: %s", self.model_name)

    def calculate(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """
        Calculate cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        self._load_model()

        # Generate embeddings
        embeddings = self._model.encode([text1, text2])

        # Calculate cosine similarity
        similarity = self._cosine_similarity(embeddings[0], embeddings[1])

        return float(similarity)

    def _cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)