"""
ArXiv Document Source

Fetches academic papers from ArXiv API with improved relevance filtering.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

import arxiv
import requests
from haystack.components.converters import PyPDFToDocument
from haystack.dataclasses import Document

from .base import DocumentSource

logger = logging.getLogger(__name__)


class ArXivSource(DocumentSource):
    """
    Fetches papers from ArXiv with intelligent relevance filtering.
    
    Features:
    - Smart query construction
    - Relevance scoring
    - Metadata enrichment
    - Duplicate detection
    """

    def __init__(
        self, 
        download_dir: Optional[Path] = None,
        min_relevance_score: float = 0.3
    ):
        """
        Initialize ArXiv source.
        
        Args:
            download_dir: Where to save PDFs (default: data/arxiv)
            min_relevance_score: Minimum relevance threshold (0.0-1.0)
        """
        if download_dir is None:
            from ...utils.config import load_config
            root = Path(__file__).resolve().parents[3]
            download_dir = root / "data" / "arxiv"
        
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.min_relevance_score = min_relevance_score

    def fetch(
        self,
        query: str,
        max_results: int = 5,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance,
    ) -> List[Document]:
        """
        Fetch papers from ArXiv with relevance filtering.
        
        Args:
            query: Search query (e.g., "machine learning")
            max_results: Maximum number of papers to fetch
            sort_by: Sorting criterion (Relevance, SubmittedDate, LastUpdatedDate)
            
        Returns:
            List of documents with enriched metadata
        """
        # Validate and clean query
        cleaned_query = self._clean_query(query)
        if not cleaned_query or len(cleaned_query) < 3:
            logger.error("Invalid query after cleaning: '%s'", query)
            return []
        
        logger.info(
            "Fetching ArXiv papers: query='%s', max_results=%d", 
            cleaned_query, 
            max_results
        )
        
        # Construct optimized ArXiv query
        arxiv_query = self._construct_arxiv_query(cleaned_query)
        logger.info("Constructed ArXiv query: %s", arxiv_query)
        
        # Search ArXiv (fetch more than needed for filtering)
        search = arxiv.Search(
            query=arxiv_query,
            max_results=max_results * 3,  # Fetch extra for filtering
            sort_by=sort_by,
            sort_order=arxiv.SortOrder.Descending,
        )
        
        # Collect papers with relevance scores
        papers_with_scores: List[Tuple[arxiv.Result, float]] = []
        
        for result in search.results():
            try:
                # Calculate relevance score
                score = self._calculate_relevance(cleaned_query, result)
                
                if score >= self.min_relevance_score:
                    papers_with_scores.append((result, score))
                    logger.debug(
                        "Paper '%s' scored %.2f (accepted)", 
                        result.title[:50], 
                        score
                    )
                else:
                    logger.debug(
                        "Paper '%s' scored %.2f (rejected)", 
                        result.title[:50], 
                        score
                    )
                    
            except Exception as e:
                logger.warning("Error scoring paper %s: %s", result.get_short_id(), e)
        
        # Sort by relevance score
        papers_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N papers
        top_papers = papers_with_scores[:max_results]
        
        if not top_papers:
            logger.warning(
                "No papers met relevance threshold (%.2f) for query: %s", 
                self.min_relevance_score,
                cleaned_query
            )
            return []
        
        logger.info(
            "Found %d relevant papers (from %d candidates) for query: %s",
            len(top_papers),
            len(papers_with_scores),
            cleaned_query
        )
        
        # Download and convert papers
        documents = []
        for paper, score in top_papers:
            try:
                # Download PDF
                pdf_path = self._download_pdf(paper)
                
                # Convert PDF to document
                doc = self._pdf_to_document(pdf_path, paper, score)
                
                if doc:
                    documents.append(doc)
                    
            except Exception as e:
                logger.warning(
                    "Failed to process ArXiv paper %s: %s",
                    paper.get_short_id(),
                    e,
                )
        
        logger.info("Successfully fetched %d documents from ArXiv", len(documents))
        
        return documents

    def _clean_query(self, query: str) -> str:
        """
        Clean and validate the query string.
        
        Args:
            query: Raw query string
            
        Returns:
            Cleaned query string
        """
        # Remove special characters that might break ArXiv search
        query = re.sub(r'[^\w\s\-]', ' ', query)
        # Remove extra whitespace
        query = ' '.join(query.split())
        return query.strip()

    def _construct_arxiv_query(self, query: str) -> str:
        """
        Construct optimized ArXiv query from user topic.
        
        Strategies:
        1. Search in title and abstract
        2. Use OR between keywords for broader results
        3. Remove stop words
        4. Limit to first 5 keywords
        
        Args:
            query: Cleaned user query
            
        Returns:
            Optimized ArXiv API query string
        """
        # Split into keywords
        keywords = query.lower().split()
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
            'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was',
            'what', 'how', 'when', 'where', 'why', 'which'
        }
        keywords = [k for k in keywords if k not in stop_words and len(k) > 2]
        
        if not keywords:
            # Fallback: use original query
            return query
        
        # Limit to first 5 most relevant keywords
        keywords = keywords[:5]
        
        # Construct query - prioritize title, then abstract
        # Use OR between keywords for broader coverage
        query_parts = []
        for kw in keywords:
            query_parts.append(f'(ti:"{kw}" OR abs:"{kw}")')
        
        arxiv_query = ' AND '.join(query_parts)
        
        return arxiv_query

    def _calculate_relevance(self, query: str, paper: arxiv.Result) -> float:
        """
        Calculate relevance score between query and paper.
        
        Scoring factors:
        - Exact phrase match in title: high weight
        - Exact phrase match in abstract: medium weight
        - Individual keyword matches: lower weight
        - Category match: bonus
        
        Args:
            query: Original query string
            paper: ArXiv paper result
            
        Returns:
            Relevance score (0.0-1.0)
        """
        query_lower = query.lower()
        query_words = set(self._clean_query(query).lower().split())
        
        title_lower = paper.title.lower()
        abstract_lower = paper.summary.lower()
        
        score = 0.0
        
        # 1. Exact phrase match (very high weight)
        if query_lower in title_lower:
            score += 1.0
            logger.debug("Exact phrase match in title: +1.0")
        elif query_lower in abstract_lower:
            score += 0.6
            logger.debug("Exact phrase match in abstract: +0.6")
        
        # 2. Individual keyword matches
        title_words = set(re.findall(r'\w+', title_lower))
        abstract_words = set(re.findall(r'\w+', abstract_lower))
        
        # Title keyword matches (high weight)
        title_matches = len(query_words.intersection(title_words))
        if len(query_words) > 0:
            title_score = (title_matches / len(query_words)) * 0.4
            score += title_score
            logger.debug("Title keyword matches: %d/%d = +%.2f", 
                        title_matches, len(query_words), title_score)
        
        # Abstract keyword matches (medium weight)
        abstract_matches = len(query_words.intersection(abstract_words))
        if len(query_words) > 0:
            abstract_score = (abstract_matches / len(query_words)) * 0.2
            score += abstract_score
            logger.debug("Abstract keyword matches: %d/%d = +%.2f",
                        abstract_matches, len(query_words), abstract_score)
        
        # 3. Category relevance bonus
        category = paper.primary_category.lower() if paper.primary_category else ""
        relevant_categories = ['cs.', 'stat.', 'math.', 'physics.', 'econ.', 'q-bio.']
        if any(cat in category for cat in relevant_categories):
            score += 0.1
            logger.debug("Category bonus: +0.1")
        
        # Normalize score to 0-1 range
        score = min(score, 1.0)
        
        return score

    def _download_pdf(self, result: arxiv.Result) -> Path:
        """
        Download PDF from ArXiv.
        
        Args:
            result: ArXiv search result
            
        Returns:
            Path to downloaded PDF
        """
        paper_id = result.get_short_id()
        title_slug = self._slugify(result.title)
        filename = f"arxiv-{paper_id}-{title_slug}.pdf"
        target = self.download_dir / filename
        
        if target.exists():
            logger.info("PDF already exists: %s", filename)
            return target
        
        logger.info("Downloading %s -> %s", result.pdf_url, filename)
        
        response = requests.get(result.pdf_url, timeout=60)
        response.raise_for_status()
        
        target.write_bytes(response.content)
        
        return target

    def _pdf_to_document(
        self, 
        pdf_path: Path, 
        arxiv_result: arxiv.Result,
        relevance_score: float
    ) -> Optional[Document]:
        """
        Convert PDF to Haystack document with ArXiv metadata.
        
        Args:
            pdf_path: Path to PDF file
            arxiv_result: ArXiv search result with metadata
            relevance_score: Calculated relevance score
            
        Returns:
            Document with enriched metadata
        """
        converter = PyPDFToDocument()
        result = converter.run(sources=[str(pdf_path)])
        
        if not result["documents"]:
            logger.warning("Failed to extract text from %s", pdf_path.name)
            return None
        
        # Haystack may return multiple docs (one per page)
        # We merge them into one document
        doc = self._merge_pages(result["documents"])
        
        # Enrich with ArXiv metadata
        meta = doc.meta or {}
        meta.update({
            "source": pdf_path.name,
            "arxiv_id": arxiv_result.get_short_id(),
            "arxiv_category": arxiv_result.primary_category,
            "authors": [author.name for author in arxiv_result.authors],
            "publication_date": arxiv_result.published.isoformat() if arxiv_result.published else None,
            "abstract": arxiv_result.summary,
            "title": arxiv_result.title,
            "pdf_url": arxiv_result.pdf_url,
            "relevance_score": relevance_score,  # Add relevance score to metadata
        })
        doc.meta = meta
        
        logger.info(
            "Processed ArXiv paper: %s (relevance: %.2f)", 
            arxiv_result.title,
            relevance_score
        )
        
        return doc

    @staticmethod
    def _merge_pages(documents: List[Document]) -> Document:
        """Merge multi-page PDF into single document."""
        if len(documents) == 1:
            return documents[0]
        
        # Merge content
        merged_content = "\n\n".join(doc.content for doc in documents)
        
        # Use first document's metadata
        merged = documents[0]
        merged.content = merged_content
        
        return merged

    @staticmethod
    def _slugify(text: str, max_len: int = 60) -> str:
        """Convert title to filesystem-safe slug."""
        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", "-", text)
        text = re.sub(r"-+", "-", text).strip("-")
        return text[:max_len] or "paper"

    def get_source_name(self) -> str:
        return "ArXiv"