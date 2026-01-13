from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from haystack.components.converters import PyPDFToDocument, TextFileToDocument
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from haystack.components.preprocessors import DocumentSplitter
from haystack.dataclasses import Document

from ..utils.config import load_config

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "raw"

DEFAULT_EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

try:
    from haystack_integrations.components.retrievers.weaviate import (
        WeaviateHybridRetriever,
    )
    from haystack_integrations.document_stores.weaviate import WeaviateDocumentStore

    HAS_WEAVIATE = True
except ImportError:  # pragma: no cover - env-specific
    WeaviateDocumentStore = None  # type: ignore[assignment]
    WeaviateHybridRetriever = None  # type: ignore[assignment]
    HAS_WEAVIATE = False


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
    Pure Weaviate-based RAG pipeline with hybrid retrieval.

    - Uses WeaviateDocumentStore to persist embedded chunks.
    - Uses SentenceTransformers embeddings for content.
    - Uses WeaviateHybridRetriever to combine vector + keyword search.

    Notes:
    - WeaviateHybridRetriever requires BOTH `query` and `query_embedding`.
      So we keep a SentenceTransformersTextEmbedder for queries.
    """

    store: Any
    retriever: Any
    text_embedder: SentenceTransformersTextEmbedder
    embedding_model: str

    @classmethod
    def from_config(cls) -> "RAGPipeline":
        """
        Build a Weaviate-backed RAG pipeline from configs.

        Uses:
        - cfg.rag.chunk_size, cfg.rag.chunk_overlap
        - cfg.weaviate.url (already env-overridden by load_config)
        - cfg.weaviate.embedding_model
        """
        cfg = load_config()

        if not HAS_WEAVIATE:
            raise RuntimeError(
                "RAGPipeline.from_config: weaviate-haystack is not installed. "
                "Install it (weaviate-haystack>=6.x) or adjust requirements."
            )

        docs = _load_documents(DATA_DIR)
        if not docs:
            raise RuntimeError(
                f"No documents found in {DATA_DIR}. "
                "Add a few PDFs or .txt files and rebuild the RAG index."
            )

        # Config sources (env overrides yaml already applied in load_config)
        rag_cfg = cfg.rag
        weav_cfg = cfg.weaviate

        emb_model = weav_cfg.embedding_model or DEFAULT_EMB_MODEL
        weaviate_url = weav_cfg.url

        logger.info(
            "RAGPipeline: initializing WeaviateDocumentStore at %s", weaviate_url
        )
        store_kwargs = {"url": weaviate_url}

        # If an API key is configured (cloud), use auth_client_secret=AuthApiKey()
        if weav_cfg.api_key:
            from weaviate.auth import AuthApiKey

            store_kwargs["auth_client_secret"] = AuthApiKey(weav_cfg.api_key)

        store = WeaviateDocumentStore(**store_kwargs)

        # Split documents into chunks
        splitter = DocumentSplitter(
            split_by="word",
            split_length=rag_cfg.chunk_size,
            split_overlap=rag_cfg.chunk_overlap,
        )
        chunks = splitter.run(documents=docs)["documents"]
        logger.info(
            "RAGPipeline: created %d chunks from %d docs", len(chunks), len(docs)
        )

        # Embed chunks and write them into Weaviate
        embedder = SentenceTransformersDocumentEmbedder(model=emb_model)
        embedder.warm_up()
        embedded_docs = embedder.run(documents=chunks)["documents"]
        store.write_documents(embedded_docs)

        logger.info(
            "RAGPipeline: indexed %d embedded chunks into Weaviate (model=%s)",
            len(embedded_docs),
            emb_model,
        )

        # Query embedder (needed because WeaviateHybridRetriever requires query embeddings)
        text_embedder = SentenceTransformersTextEmbedder(model=emb_model)
        text_embedder.warm_up()

        retriever = WeaviateHybridRetriever(document_store=store)

        return cls(
            store=store,
            retriever=retriever,
            text_embedder=text_embedder,
            embedding_model=emb_model,
        )

    def run(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Retrieve top-k relevant chunks for the query via WeaviateHybridRetriever.
        """
        logger.info(
            "RAGPipeline: retrieving top_k=%d for query='%s' (backend=weaviate-hybrid)",
            top_k,
            query,
        )

        # Hybrid retriever needs BOTH query and query_embedding
        emb_res = self.text_embedder.run(text=query)
        query_embedding = emb_res["embedding"]

        result = self.retriever.run(
            query=query, query_embedding=query_embedding, top_k=top_k
        )

        docs = result.get("documents", [])
        logger.info("RAGPipeline: retrieved %d documents", len(docs))
        return docs
