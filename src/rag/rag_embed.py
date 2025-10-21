from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import List

from haystack.dataclasses import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.converters import PyPDFToDocument, TextFileToDocument
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from ollama import chat
from utils.config import load_config

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "raw"
OUTPUTS = ROOT / "outputs"

OLLAMA_HOST = load_config().llm.host
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

QUESTION = (
    "Give me a concise 6–8 sentence overview across these docs and cite filenames as [1], [2], ..."
)

def load_docs() -> List[Document]:
    docs: List[Document] = []
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    txts = sorted(DATA_DIR.glob("*.txt"))

    if pdfs:
        docs += PyPDFToDocument().run(paths=[str(p) for p in pdfs])["documents"]
    if txts:
        docs += TextFileToDocument(encoding="utf-8").run(paths=[str(t) for t in txts])["documents"]

    for d in docs:
        meta = getattr(d, "metadata", {}) or {}
        src = meta.get("file_path") or meta.get("file_name") or meta.get("source")
        if src:
            meta["source"] = Path(src).name
        d.metadata = meta
    return docs

def build_store(docs: List[Document], chunk_size: int, chunk_overlap: int) -> InMemoryEmbeddingRetriever:
    splitter = DocumentSplitter(split_by="word", split_length=chunk_size, split_overlap=chunk_overlap)
    chunks = splitter.run(documents=docs)["documents"]

    store = InMemoryDocumentStore()
    doc_embedder = SentenceTransformersDocumentEmbedder(model=EMB_MODEL)
    doc_embedder.warm_up()
    chunks = doc_embedder.run(documents=chunks)["documents"]
    store.write_documents(chunks)

    retriever = InMemoryEmbeddingRetriever(
        document_store=store,
        top_k=5,
        text_embedder=SentenceTransformersTextEmbedder(model=EMB_MODEL),
    )
    return retriever

def call_ollama(context: List[Document], question: str, model_name: str) -> str:
    uniq, lines = [], []
    for d in context:
        src = d.metadata.get("source", "unknown")
        if src not in uniq:
            uniq.append(src)
        idx = uniq.index(src) + 1
        lines.append(f"[{idx}] {d.content.strip()}")

    context_txt = "\n\n".join(lines[:8])
    src_map = "\n".join(f"[{i+1}] {s}" for i, s in enumerate(uniq))

    prompt = (
        "Use ONLY the context. If unsure, say you are unsure.\n\n"
        f"Question:\n{question}\n\n"
        f"Context:\n{context_txt}\n\n"
        "Write 6–8 sentences and include inline citations [1], [2] that match the source labels."
    )
    try:
        r = chat(model=model_name, messages=[{"role": "user", "content": prompt}])
        answer = r.message.content.strip()
    except Exception as e:
        print(f"⚠️  Could not reach Ollama at {OLLAMA_HOST}. Is the app running?")
        print(f"Error details: {e}")
    answer = f"❌ Ollama connection failed. Please start Ollama and retry.\n\nDetails: {e}"
    return answer + ("\n\nSources:\n" + src_map if src_map else "\n\nSources: (none)")

def main():
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    cfg = load_config()

    docs = load_docs()
    if not docs:
        print(f"No docs in {DATA_DIR}")
        return

    retriever = build_store(docs, cfg.rag.chunk_size, cfg.rag.chunk_overlap)
    result = retriever.run(query=QUESTION, top_k=cfg.rag.top_k)["documents"]
    answer = call_ollama(result, QUESTION, cfg.llm.model)

    out = OUTPUTS / f"rag_embed_inmem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    out.write_text(answer, encoding="utf-8")
    print("✅ RAG (in-memory embeddings) complete\nSaved:", out, "\n")
    print(answer)

if __name__ == "__main__":
    main()