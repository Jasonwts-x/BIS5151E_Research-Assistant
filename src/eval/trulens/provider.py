"""
TruLens Provider
Custom feedback provider using local LLM (Ollama).
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LocalLLMProvider:
    """
    Custom TruLens provider using local Ollama LLM.
    
    This provider can be used instead of OpenAI for feedback functions.
    """

    def __init__(
        self,
        model: str = "qwen3:4b",
        base_url: str = "http://ollama:11434",
    ):
        """
        Initialize provider.

        Args:
            model: Ollama model name
            base_url: Ollama base URL
        """
        self.model = model
        self.base_url = base_url
        logger.info("LocalLLMProvider initialized: %s at %s", model, base_url)

    def groundedness(
        self,
        context: str,
        answer: str,
    ) -> float:
        """
        Measure groundedness: Is answer supported by context?

        Args:
            context: Retrieved context
            answer: Generated answer

        Returns:
            Score between 0 and 1
        """
        # TODO: Implement using local LLM
        # For now, simple heuristic
        
        # Check if answer contains citations
        import re
        citations = re.findall(r'\[(\d+)\]', answer)
        
        if not citations:
            return 0.3  # Low score without citations
        
        # Simple keyword overlap
        context_words = set(context.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(context_words & answer_words)
        
        if len(answer_words) == 0:
            return 0.0
        
        score = min(1.0, overlap / len(answer_words))
        return score

    def relevance(
        self,
        query: str,
        answer: str,
    ) -> float:
        """
        Measure answer relevance to query.

        Args:
            query: User query
            answer: Generated answer

        Returns:
            Score between 0 and 1
        """
        # TODO: Implement using local LLM or embeddings
        
        # Simple keyword overlap
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(query_words & answer_words)
        
        if len(query_words) == 0:
            return 0.0
        
        score = min(1.0, overlap / len(query_words))
        return max(0.3, score)  # Minimum baseline score

    def context_relevance(
        self,
        query: str,
        context: str,
    ) -> float:
        """
        Measure context relevance to query.

        Args:
            query: User query
            context: Retrieved context

        Returns:
            Score between 0 and 1
        """
        # TODO: Implement using local LLM or embeddings
        
        # Simple keyword overlap
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())
        overlap = len(query_words & context_words)
        
        if len(query_words) == 0:
            return 0.0
        
        score = min(1.0, overlap / len(query_words))
        return max(0.4, score)  # Minimum baseline score