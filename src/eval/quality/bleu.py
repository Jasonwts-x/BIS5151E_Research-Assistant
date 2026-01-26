"""
BLEU Score Calculator
Measures precision of n-gram matches.
"""
from __future__ import annotations

import logging
import math
from collections import Counter
from typing import List

logger = logging.getLogger(__name__)


class BLEUCalculator:
    """
    Calculate BLEU scores for text comparison.
    
    BLEU (Bilingual Evaluation Understudy) measures precision of
    n-gram matches between generated and reference text.
    """

    def __init__(self, max_n: int = 4):
        """
        Initialize calculator.
        
        Args:
            max_n: Maximum n-gram size (default: 4)
        """
        self.max_n = max_n
        logger.info("BLEUCalculator initialized (max_n=%d)", max_n)

    def calculate(
        self,
        generated: str,
        reference: str,
    ) -> float:
        """
        Calculate BLEU score.
        
        Args:
            generated: Generated text
            reference: Reference text
            
        Returns:
            BLEU score (0-1)
        """
        # Tokenize
        generated_tokens = generated.lower().split()
        reference_tokens = reference.lower().split()

        if not generated_tokens or not reference_tokens:
            return 0.0

        # Calculate brevity penalty
        bp = self._brevity_penalty(generated_tokens, reference_tokens)

        # Calculate n-gram precisions
        precisions = []
        for n in range(1, self.max_n + 1):
            precision = self._calculate_ngram_precision(
                generated_tokens, reference_tokens, n
            )
            if precision > 0:
                precisions.append(precision)
            else:
                # If any n-gram has 0 precision, BLEU is 0
                return 0.0

        # Geometric mean of precisions
        if not precisions:
            return 0.0

        log_precision_sum = sum(math.log(p) for p in precisions)
        geo_mean = math.exp(log_precision_sum / len(precisions))

        # BLEU score
        bleu = bp * geo_mean
        return bleu

    def _brevity_penalty(
        self,
        generated_tokens: List[str],
        reference_tokens: List[str],
    ) -> float:
        """
        Calculate brevity penalty.
        
        Penalizes generated text that is shorter than reference.
        """
        gen_len = len(generated_tokens)
        ref_len = len(reference_tokens)

        if gen_len >= ref_len:
            return 1.0

        return math.exp(1 - ref_len / gen_len)

    def _calculate_ngram_precision(
        self,
        generated_tokens: List[str],
        reference_tokens: List[str],
        n: int,
    ) -> float:
        """
        Calculate precision for n-grams.
        
        Args:
            generated_tokens: Generated text tokens
            reference_tokens: Reference text tokens
            n: N-gram size
            
        Returns:
            Precision score
        """
        # Generate n-grams
        gen_ngrams = self._get_ngrams(generated_tokens, n)
        ref_ngrams = self._get_ngrams(reference_tokens, n)

        if not gen_ngrams:
            return 0.0

        # Count matches (with clipping)
        matches = 0
        for ngram in gen_ngrams:
            matches += min(gen_ngrams[ngram], ref_ngrams.get(ngram, 0))

        # Precision
        total_ngrams = sum(gen_ngrams.values())
        precision = matches / total_ngrams if total_ngrams > 0 else 0.0

        return precision

    def _get_ngrams(self, tokens: List[str], n: int) -> Counter:
        """Get n-gram counts from token list."""
        ngrams = Counter()
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i + n])
            ngrams[ngram] += 1
        return ngrams