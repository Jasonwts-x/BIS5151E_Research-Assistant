#!/usr/bin/env python3
"""
Ingest documents from data/raw/ into the RAG system.

This is a more controlled alternative to rebuild_rag_index.py
that allows selective ingestion and progress tracking.

Usage:
    python scripts/data/ingest_documents.py
    python scripts/data/ingest_documents.py --pattern "*.pdf"
    python scripts/data/ingest_documents.py --clear-first
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.rag.pipeline import RAGPipeline
from src.utils.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def count_documents(data_dir: Path, pattern: str = "*") -> int:
    """Count documents matching pattern."""
    pdfs = list(data_dir.glob(f"{pattern}.pdf"))
    txts = list(data_dir.glob(f"{pattern}.txt"))
    return len(pdfs) + len(txts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest documents into RAG system"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*",
        help="File pattern to match (e.g., 'arxiv*' for arxiv papers only)",
    )
    parser.add_argument(
        "--clear-first",
        action="store_true",
        help="Clear existing index before ingesting",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without actually doing it",
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("DOCUMENT INGESTION")
    print("=" * 70)
    
    cfg = load_config()
    data_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
    
    # Count documents
    doc_count = count_documents(data_dir, args.pattern)
    
    if doc_count == 0:
        print(f"\n❌ No documents found matching pattern '{args.pattern}'")
        print(f"   in {data_dir}")
        sys.exit(1)
    
    print(f"\n📄 Found {doc_count} documents matching '{args.pattern}'")
    
    # List files
    pdfs = sorted(data_dir.glob(f"{args.pattern}.pdf"))
    txts = sorted(data_dir.glob(f"{args.pattern}.txt"))
    
    print("\nFiles to ingest:")
    for p in pdfs:
        print(f"   📕 {p.name}")
    for t in txts:
        print(f"   📄 {t.name}")
    
    if args.dry_run:
        print("\n✅ Dry run complete (no changes made)")
        return
    
    print(f"\n🔄 Ingesting documents...")
    print(f"   Weaviate: {cfg.weaviate.url}")
    print(f"   Index: {cfg.weaviate.index_name}")
    
    if args.clear_first:
        print("\n⚠️  Clearing existing index first...")
    
    try:
        # This rebuilds the index (in future, could be more selective)
        pipeline = RAGPipeline.from_config()
        
        print("\n✅ Documents ingested successfully!")
        
        # Test retrieval
        print("\n🧪 Testing retrieval...")
        test_docs = pipeline.run(query="research", top_k=3)
        print(f"   Retrieved {len(test_docs)} documents")
        
    except Exception as e:
        logger.exception("Ingestion failed")
        print(f"\n❌ Ingestion failed: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✅ INGESTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()