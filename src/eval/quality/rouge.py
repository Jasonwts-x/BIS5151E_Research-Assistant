"""
ROUGE Score Calculator
Measures overlap between generated and reference text.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ROUGECalculator:
    """
    Calculate ROUGE scores for text comparison.
    
    ROUGE (Recall-Oriented Understudy for Gisting Evaluation) measures
    overlap between generated text and reference text.
    """

    def __init__(self):
        """Initialize calculator."""
        logger.info("ROUGECalculator initialized")

    def calculate(
        self,
        generated: str,
        reference: str,
    ) -> Dict[str, float]:
        """
        Calculate ROUGE scores.
        
        Args:
            generated: Generated text
            reference: Reference text
            
        Returns:
            Dictionary with rouge-1, rouge-2, rouge-l scores
        """
        # Simple implementation - for production, use rouge-score library
        generated_tokens = generated.lower().split()
        reference_tokens = reference.lower().split()

        # ROUGE-1 (unigram overlap)
        rouge1 = self._calculate_rouge_n(generated_tokens, reference_tokens, n=1)

        # ROUGE-2 (bigram overlap)
        rouge2 = self._calculate_rouge_n(generated_tokens, reference_tokens, n=2)

        # ROUGE-L (longest common subsequence)
        rouge_l = self._calculate_rouge_l(generated_tokens, reference_tokens)

        return {
            "rouge-1": rouge1,
            "rouge-2": rouge2,
            "rouge-l": rouge_l,
        }

    def _calculate_rouge_n(
        self,
        generated_tokens: List[str],
        reference_tokens: List[str],
        n: int = 1,
    ) -> float:
        """
        Calculate ROUGE-N score.
        
        Args:
            generated_tokens: Generated text tokens
            reference_tokens: Reference text tokens
            n: N-gram size
            
        Returns:
            ROUGE-N F1 score
        """
        if not generated_tokens or not reference_tokens:
            return 0.0

        # Generate n-grams
        gen_ngrams = self._get_ngrams(generated_tokens, n)
        ref_ngrams = self._get_ngrams(reference_tokens, n)

        if not gen_ngrams or not ref_ngrams:
            return 0.0

        # Calculate overlap
        overlap = len(gen_ngrams & ref_ngrams)

        # Precision and recall
        precision = overlap / len(gen_ngrams) if gen_ngrams else 0
        recall = overlap / len(ref_ngrams) if ref_ngrams else 0

        # F1 score
        if precision + recall == 0:
            return 0.0

        f1 = 2 * (precision * recall) / (precision + recall)
        return f1

    def _calculate_rouge_l(
        self,
        generated_tokens: List[str],
        reference_tokens: List[str],
    ) -> float:
        """
        Calculate ROUGE-L score (longest common subsequence).
        
        Args:
            generated_tokens: Generated text tokens
            reference_tokens: Reference text tokens
            
        Returns:
            ROUGE-L F1 score
        """
        if not generated_tokens or not reference_tokens:
            return 0.0

        # Calculate LCS length
        lcs_length = self._lcs_length(generated_tokens, reference_tokens)

        # Precision and recall
        precision = lcs_length / len(generated_tokens) if generated_tokens else 0
        recall = lcs_length / len(reference_tokens) if reference_tokens else 0

        # F1 score
        if precision + recall == 0:
            return 0.0

        f1 = 2 * (precision * recall) / (precision + recall)
        return f1

    def _get_ngrams(self, tokens: List[str], n: int) -> set:
        """Get n-grams from token list."""
        ngrams = set()
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i + n])
            ngrams.add(ngram)
        return ngrams

    def _lcs_length(self, seq1: List[str], seq2: List[str]) -> int:
        """Calculate longest common subsequence length."""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return dp[m][n]