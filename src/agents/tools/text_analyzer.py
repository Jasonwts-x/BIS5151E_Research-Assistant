"""
Text Quality Analysis Tool.

Analyzes text for quality metrics to help Reviewer agent.
Provides objective measurements for text improvement.

Architecture:
    Statistical analysis of text characteristics.
    Generates quality score and improvement suggestions.
"""
from __future__ import annotations

import re
from typing import Dict

from crewai.tools import tool


@tool
def analyze_text_quality(text: str) -> Dict[str, any]:
    """
    Analyze text for quality metrics.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with metrics (word_count, citation_density, quality_score, suggestions)
    """
    # Word count
    words = text.split()
    word_count = len(words)
    
    # Sentence count (split on . ! ?)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)
    
    # Average sentence length
    avg_sentence_length = word_count / max(1, sentence_count)
    
    # Citation count
    citations = re.findall(r'\[\d+\]', text)
    citation_count = len(citations)
    
    # Citation density (per 100 words)
    citation_density = (citation_count / max(1, word_count)) * 100
    
    # Check for references section
    has_references = bool(
        re.search(r'##\s*(References|Literaturverzeichnis|Références)', text, re.IGNORECASE)
    )
    
    # Quality score calculation (0-1)
    # Factors: reasonable length, good citation density, has references
    length_score = min(1.0, word_count / 300)  # Target: 300+ words
    citation_score = min(1.0, citation_density / 3.0)  # Target: 3+ citations per 100 words
    structure_score = 1.0 if has_references else 0.5
    
    quality_score = (length_score * 0.3 + citation_score * 0.4 + structure_score * 0.3)
    
    # Generate suggestions
    suggestions = []
    
    if word_count < 200:
        suggestions.append("Text is short. Consider expanding with more details.")
    elif word_count > 500:
        suggestions.append("Text is long. Consider condensing to improve readability.")
    
    if avg_sentence_length > 25:
        suggestions.append("Average sentence length is high. Break down complex sentences.")
    elif avg_sentence_length < 10:
        suggestions.append("Sentences are very short. Combine some for better flow.")
    
    if citation_density < 2.0:
        suggestions.append("Low citation density. Add more citations to support claims.")
    elif citation_density > 10.0:
        suggestions.append("Very high citation density. Some citations may be redundant.")
    
    if not has_references:
        suggestions.append("Add a References section at the end with full source details.")
    
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_length, 1),
        "citation_count": citation_count,
        "citation_density": round(citation_density, 2),
        "has_references": has_references,
        "quality_score": round(quality_score, 2),
        "suggestions": suggestions,
    }