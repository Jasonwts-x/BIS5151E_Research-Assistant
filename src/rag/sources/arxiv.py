"""
ArXiv Document Source

Fetches academic papers from ArXiv API.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional

import arxiv
import requests
from haystack.components.converters import PyPDFToDocument
from haystack.dataclasses import Document

from .base import DocumentSource

logger = logging.getLogger(__name__)


class ArXivSource(DocumentSource):
    """
    Fetches papers from ArXiv.
    
    Features:
    - Downloads PDFs
    - Extracts metadata (authors, date, category, abstract)
    - Enriches documents for better retrieval
    """

    def __init__(self, download_dir: Optional[Path] = None):
        """
        Initialize ArXiv source.
        
        Args:
            download_dir: Where to save PDFs (default: data/raw)
        """
        if download_dir is None:
            from ...utils.config import load_config
            root = Path(__file__).resolve().parents[3]
            download_dir = root / "data" / "raw"
        
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def fetch(
        self,
        query: str,
        max_results: int = 5,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance,
    ) -> List[Document]:
        """
        Fetch papers from ArXiv.
        
        Args:
            query: Search query (e.g., "machine learning")
            max_results: Maximum number of papers to fetch
            sort_by: Sorting criterion (Relevance, SubmittedDate, LastUpdatedDate)
            
        Returns:
            List of documents with enriched metadata
        """
        logger.info("Fetching ArXiv papers: query='%s', max_results=%d", query, max_results)
        
        # Search ArXiv
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=arxiv.SortOrder.Descending,
        )
        
        documents = []
        
        for result in search.results():
            try:
                # Download PDF
                pdf_path = self._download_pdf(result)
                
                # Convert PDF to document
                doc = self._pdf_to_document(pdf_path, result)
                
                if doc:
                    documents.append(doc)
                    
            except Exception as e:
                logger.warning(
                    "Failed to process ArXiv paper %s: %s",
                    result.get_short_id(),
                    e,
                )
        
        logger.info("Fetched %d documents from ArXiv", len(documents))
        
        return documents

    def _download_pdf(self, result: arxiv.Result) -> Path:
        """
        Download PDF from ArXiv.
        
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

    def _pdf_to_document(self, pdf_path: Path, arxiv_result: arxiv.Result) -> Optional[Document]:
        """
        Convert PDF to Haystack document with ArXiv metadata.
        
        Args:
            pdf_path: Path to PDF file
            arxiv_result: ArXiv search result with metadata
            
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
        })
        doc.meta = meta
        
        logger.info("Processed ArXiv paper: %s", arxiv_result.title)
        
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