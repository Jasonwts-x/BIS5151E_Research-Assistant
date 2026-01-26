"""
TruLens Feedback Functions
Custom feedback functions for evaluation.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class FeedbackProvider:
    """Provides feedback functions for TruLens evaluation."""

    def __init__(self, provider: Optional[object] = None):
        """
        Initialize feedback provider.

        Args:
            provider: Optional LLM provider (LocalLLMProvider or OpenAI)
        """
        if provider is None:
            from .provider import LocalLLMProvider
            provider = LocalLLMProvider()
        
        self.provider = provider
        logger.info("FeedbackProvider initialized")

    def groundedness_score(
        self,
        context: str,
        answer: str,
    ) -> tuple[float, str]:
        """
        Calculate groundedness score with reasoning.

        Args:
            context: Retrieved context
            answer: Generated answer

        Returns:
            (score, reasoning) tuple
        """
        score = self.provider.groundedness(context, answer)
        
        # Generate reasoning
        citations = re.findall(r'\[(\d+)\]', answer)
        
        if not citations:
            reasoning = "Answer lacks citations to support claims."
        elif score > 0.7:
            reasoning = f"Answer well-grounded with {len(citations)} citations."
        elif score > 0.4:
            reasoning = f"Answer partially grounded with {len(citations)} citations."
        else:
            reasoning = "Answer poorly grounded in provided context."
        
        return score, reasoning

    def relevance_score(
        self,
        query: str,
        answer: str,
    ) -> tuple[float, str]:
        """
        Calculate answer relevance score with reasoning.

        Args:
            query: User query
            answer: Generated answer

        Returns:
            (score, reasoning) tuple
        """
        score = self.provider.relevance(query, answer)
        
        # Generate reasoning
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(query_words & answer_words)
        
        if score > 0.7:
            reasoning = f"Answer highly relevant ({overlap} shared terms)."
        elif score > 0.4:
            reasoning = f"Answer moderately relevant ({overlap} shared terms)."
        else:
            reasoning = f"Answer relevance low ({overlap} shared terms)."
        
        return score, reasoning

    def context_relevance_score(
        self,
        query: str,
        context: str,
    ) -> tuple[float, str]:
        """
        Calculate context relevance score with reasoning.

        Args:
            query: User query
            context: Retrieved context

        Returns:
            (score, reasoning) tuple
        """
        score = self.provider.context_relevance(query, context)
        
        # Generate reasoning
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())
        overlap = len(query_words & context_words)
        
        if score > 0.7:
            reasoning = f"Context highly relevant ({overlap} matching terms)."
        elif score > 0.4:
            reasoning = f"Context moderately relevant ({overlap} matching terms)."
        else:
            reasoning = f"Context relevance low ({overlap} matching terms)."
        
        return score, reasoning

    def citation_quality_score(
        self,
        answer: str,
    ) -> tuple[float, str]:
        """
        Calculate citation quality score.

        Args:
            answer: Generated answer

        Returns:
            (score, reasoning) tuple
        """
        # Find all citations
        citations = re.findall(r'\[(\d+)\]', answer)
        
        if not citations:
            return 0.0, "No citations found in answer."
        
        citation_nums = [int(c) for c in citations]
        unique_citations = len(set(citation_nums))
        
        # Check sequential numbering
        max_citation = max(citation_nums)
        expected = set(range(1, max_citation + 1))
        actual = set(citation_nums)
        missing = expected - actual
        
        # Calculate score
        if not missing and citation_nums[0] == 1:
            score = 1.0
            reasoning = f"Excellent citation quality: {unique_citations} sources, sequential."
        elif not missing:
            score = 0.8
            reasoning = f"Good citations: {unique_citations} sources, but doesn't start at [1]."
        else:
            score = 0.5
            reasoning = f"Citation issues: missing {len(missing)} numbers."
        
        return score, reasoning