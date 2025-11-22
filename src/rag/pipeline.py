from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

from haystack.components.converters import PyPDFToDocument, TextFileToDocument
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.dataclasses import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore

from ..utils.config import load_config

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "raw"


def _load_documents(data_dir: Path) -> List[Document]:
    """
    Load PDFs and text files from data/raw/ into Haystack Document objects.
    Normalizes metadata['source'] so we can later cite filenames.
    """
    docs: List[Document] = []
    pdfs = sorted(data_dir.glob("*.pdf"))
    txts = sorted(data_dir.glob("*.txt"))

    if pdfs:
        pdf_conv = PyPDFToDocument()
        for p in pdfs:
            docs += pdf_conv.run(sources=[str(p)])["documents"]

    if txts:
        txt_conv = TextFileToDocument(encoding="utf-8")
        for t in txts:
            docs += txt_conv.run(sources=[str(t)])["documents"]

    for d in docs:
        meta = getattr(d, "meta", {}) or {}
        src = meta.get("file_path") or meta.get("file_name") or meta.get("source")
        if src:
            meta["source"] = Path(src).name
        d.meta = meta

    logger.info("RAGPipeline: loaded %d base documents", len(docs))
    return docs


@dataclass
class RAGPipeline:
    """
    Simple Haystack RAG pipeline (BM25 over in-memory store).
    """

    store: InMemoryDocumentStore
    retriever: InMemoryBM25Retriever

    @classmethod
    def from_config(cls) -> "RAGPipeline":
        """
        Factory: build pipeline from configs (chunk size, overlap, etc.).
        Call this once at startup and reuse the instance.
        """
        cfg = load_config()
        docs = _load_documents(DATA_DIR)

        if not docs:
            raise RuntimeError(
                f"No documents found in {DATA_DIR}. "
                "Add a few PDFs or .txt files and rebuild the RAG index."
            )

        splitter = DocumentSplitter(
            split_by="word",
            split_length=cfg.rag.chunk_size,
            split_overlap=cfg.rag.chunk_overlap,
        )
        chunks = splitter.run(documents=docs)["documents"]

        store = InMemoryDocumentStore()
        store.write_documents(chunks)
        retriever = InMemoryBM25Retriever(document_store=store)

        logger.info(
            "RAGPipeline: built BM25 index with %d chunks (chunk_size=%d, overlap=%d)",
            len(chunks),
            cfg.rag.chunk_size,
            cfg.rag.chunk_overlap,
        )
        return cls(store=store, retriever=retriever)

    def run(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Retrieve top-k relevant chunks for the query.
        """
        logger.info("RAGPipeline: retrieving top_k=%d for query='%s'", top_k, query)
        result = self.retriever.run(query=query, top_k=top_k)
        return result.get("documents", [])
