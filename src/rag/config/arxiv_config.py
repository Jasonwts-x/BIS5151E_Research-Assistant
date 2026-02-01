"""
ArXiv Configuration

Configurable parameters for ArXiv search and relevance filtering.
"""
from dataclasses import dataclass


@dataclass
class ArXivConfig:
    """Configuration for ArXiv document source."""
    
    min_relevance_score: float = 0.3
    """Minimum relevance score threshold (0.0-1.0)"""
    
    max_keywords: int = 5
    """Maximum number of keywords to use in ArXiv query"""
    
    stop_words: set = None
    """Stop words to remove from queries"""
    
    exact_phrase_title_weight: float = 1.0
    """Weight for exact phrase match in title"""
    
    exact_phrase_abstract_weight: float = 0.6
    """Weight for exact phrase match in abstract"""
    
    title_keyword_weight: float = 0.4
    """Weight for individual keyword matches in title"""
    
    abstract_keyword_weight: float = 0.2
    """Weight for individual keyword matches in abstract"""
    
    category_bonus: float = 0.1
    """Bonus score for relevant categories"""
    
    def __post_init__(self):
        if self.stop_words is None:
            self.stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was',
                'what', 'how', 'when', 'where', 'why', 'which'
            }

DEFAULT_ARXIV_CONFIG = ArXivConfig()