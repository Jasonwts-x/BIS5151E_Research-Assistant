"""
Local File Document Source

Loads documents from local filesystem (data/raw/).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from haystack.components.converters import PyPDFToDocument, TextFileToDocument
from haystack.dataclasses import Document

from .base import DocumentSource

logger = logging.getLogger(__name__)


class LocalFileSource(DocumentSource):
    """
    Loads documents from local filesystem.
    
    Supports: PDF, TXT files from multiple directories
    """

    def __init__(self, data_dir: Path):
        """
        Initialize local file source.
        
        Args:
            data_dirs: Single directory or list of directories containing documents
        """
        if isinstance(data_dirs, Path):
            self.data_dirs = [data_dirs]
        else:
            self.data_dirs = data_dirs

    def fetch(self, pattern: str = "*") -> List[Document]:
        """
        Load documents from data directory.
        
        Args:
            pattern: Glob pattern for file matching (default: all files)
            
        Returns:
            List of documents with normalized metadata
        """
        docs: List[Document] = []
        
        # Collect files from all directories
        all_pdfs = []
        all_txts = []
        
        for data_dir in self.data_dirs:
            if not data_dir.exists():
                logger.warning("Directory does not exist: %s", data_dir)
                continue
                
            pdfs = sorted(data_dir.glob(f"{pattern}.pdf"))
            txts = sorted(data_dir.glob(f"{pattern}.txt"))
            
            all_pdfs.extend(pdfs)
            all_txts.extend(txts)
            
            logger.info(
                "Found %d PDFs and %d TXT files in %s",
                len(pdfs),
                len(txts),
                data_dir,
            )
        
        logger.info(
            "Total: Found %d PDFs and %d TXT files across all directories",
            len(all_pdfs),
            len(all_txts),
        )
        
        # Load PDFs
        if pdfs:
            pdf_conv = PyPDFToDocument()
            for pdf in all_pdfs:
                try:
                    result = pdf_conv.run(sources=[str(pdf)])
                    docs.extend(result["documents"])
                except Exception as e:
                    logger.warning("Failed to load PDF %s: %s", pdf.name, e)
        
        # Load TXT files
        if all_txts:
            txt_conv = TextFileToDocument(encoding="utf-8")
            for txt in all_txts:
                try:
                    result = txt_conv.run(sources=[str(txt)])
                    docs.extend(result["documents"])
                except Exception as e:
                    logger.warning("Failed to load TXT %s: %s", txt.name, e)
        
        # Normalize metadata
        for doc in docs:
            self._normalize_metadata(doc)
        
        logger.info("Loaded %d documents from local files", len(docs))
        
        return docs

    def _normalize_metadata(self, doc: Document) -> None:
        """Ensure consistent metadata structure."""
        meta = doc.meta or {}
        
        # Extract source filename
        source_path = meta.get("file_path") or meta.get("file_name") or meta.get("source")
        if source_path:
            meta["source"] = Path(source_path).name
        else:
            meta["source"] = "unknown"
        
        doc.meta = meta

    def get_source_name(self) -> str:
        dir_names = ", ".join(str(d) for d in self.data_dirs)
        return f"LocalFiles({dir_names})"