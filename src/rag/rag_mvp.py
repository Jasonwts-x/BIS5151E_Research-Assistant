from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import List

from haystack.dataclasses import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.converters import PyPDFToDocument, TextFileToDocument
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from ollama import chat
from utils.config import load_config

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "raw"
OUTPUTS = ROOT / "outputs"

OLLAMA_HOST = load_config().llm.host

QUESTION = (
    "Give me a concise 5–7 sentence overview of the key ideas across these docs "
    "and cite the filenames as [1], [2], ..."
)

def load_documents() -> List[Document]:
    docs: List[Document] = []
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    txts = sorted(DATA_DIR.glob("*.txt"))

    if pdfs:
        pdf_conv = PyPDFToDocument()  # requires pypdf
        for p in pdfs:
            docs += pdf_conv.run(paths=[str(p)])["documents"]

    if txts:
        txt_conv = TextFileToDocument(encoding="utf-8")
        for t in txts:
            docs += txt_conv.run(paths=[str(t)])["documents"]

    # normalize source meta for citations
    for d in docs:
        meta = getattr(d, "metadata", {}) or {}
        src = meta.get("file_path") or meta.get("file_name") or meta.get("source")
        if src:
            meta["source"] = Path(src).name
        d.metadata = meta
    return docs

def build_index(docs: List[Document], chunk_size: int, chunk_overlap: int):
    store = InMemoryDocumentStore()
    splitter = DocumentSplitter(split_by="word", split_length=chunk_size, split_overlap=chunk_overlap)
    chunks = splitter.run(documents=docs)["documents"]
    store.write_documents(chunks)
    retriever = InMemoryBM25Retriever(document_store=store)
    return retriever

def answer_with_ollama(chunks: List[Document], question: str, model_name: str) -> str:
    unique_sources, lines = [], []
    for d in chunks:
        src = d.metadata.get("source", "unknown")
        if src not in unique_sources:
            unique_sources.append(src)
        idx = unique_sources.index(src) + 1
        lines.append(f"[{idx}] {d.content.strip()}")

    context = "\n\n".join(lines[:8])
    source_map = "\n".join(f"[{i+1}] {s}" for i, s in enumerate(unique_sources))

    prompt = (
        "You are a helpful academic assistant.\n"
        "Use ONLY the context below. If unsure, say you are unsure.\n\n"
        f"Question:\n{question}\n\n"
        f"Context:\n{context}\n\n"
        "Instructions:\n"
        "- Write 5–7 sentences.\n"
        "- Include inline citations like [1], [2] that match the source labels.\n"
        "- Do not fabricate citations.\n"
    )
    try:
        res = chat(model=model_name, messages=[{"role": "user", "content": prompt}])
        answer = res.message.content.strip()
    except Exception as e:
        print(f"⚠️  Could not reach Ollama at {OLLAMA_HOST}. Is the app running?")
        print(f"Error details: {e}")
        return f"❌ Ollama connection failed. Please start Ollama and retry.\n\nDetails: {e}"
    return answer + ("\n\nSources:\n" + source_map if source_map else "\n\nSources: (none)")

def main():
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    cfg = load_config()  # ← read model & RAG params

    docs = load_documents()
    if not docs:
        print(f"No docs in {DATA_DIR}. Add a couple of PDFs or .txt and re-run.")
        return

    retriever = build_index(docs, cfg.rag.chunk_size, cfg.rag.chunk_overlap)
    top = retriever.run(query=QUESTION, top_k=cfg.rag.top_k)["documents"]
    final = answer_with_ollama(top, QUESTION, cfg.llm.model)

    out = OUTPUTS / f"rag_mvp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    out.write_text(final, encoding="utf-8")
    print("✅ RAG MVP complete\nSaved:", out, "\n")
    print(final)

if __name__ == "__main__":
    main()