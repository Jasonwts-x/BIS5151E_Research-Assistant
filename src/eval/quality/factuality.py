"""
Factuality Checker
Check if claims are factually grounded in context.
"""
from __future__ import annotations

import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)


class FactualityChecker:
    """
    Check factual accuracy of generated text.
    
    Verifies that claims in the answer are supported by the context.
    """

    def __init__(self):
        """Initialize checker."""
        logger.info("FactualityChecker initialized")

    def check(
        self,
        answer: str,
        context: str,
    ) -> Tuple[float, List[str]]:
        """
        Check factual accuracy of answer against context.
        
        Args:
            answer: Generated answer
            context: Retrieved context
            
        Returns:
            (score, issues) - Factuality score and list of issues
        """
        issues = []

        # Check 1: Citations present
        citations = re.findall(r'\[(\d+)\]', answer)
        if not citations:
            issues.append("No citations - claims cannot be verified")
            return 0.3, issues

        # Check 2: No hallucination markers
        hallucination_patterns = [
            r'\bI think\b',
            r'\bI believe\b',
            r'\bIn my opinion\b',
            r'\bas an AI\b',
        ]

        for pattern in hallucination_patterns:
            if re.search(pattern, answer, re.IGNORECASE):
                issues.append(f"Hallucination marker found: {pattern}")

        # Check 3: Keyword overlap (simple heuristic)
        context_lower = context.lower()
        answer_sentences = re.split(r'[.!?]+', answer)

        unsupported_sentences = 0
        for sentence in answer_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Extract key terms (words > 4 characters)
            key_terms = [
                word for word in sentence.lower().split()
                if len(word) > 4 and word.isalpha()
            ]

            # Check if at least 30% of key terms appear in context
            if key_terms:
                overlap = sum(1 for term in key_terms if term in context_lower)
                overlap_ratio = overlap / len(key_terms)

                if overlap_ratio < 0.3:
                    unsupported_sentences += 1

        # Calculate score
        total_sentences = len([s for s in answer_sentences if s.strip()])
        if total_sentences == 0:
            return 0.0, issues

        support_ratio = 1 - (unsupported_sentences / total_sentences)

        # Adjust score based on issues
        score = support_ratio
        if issues:
            score *= 0.7  # Penalize for hallucination markers

        return score, issues