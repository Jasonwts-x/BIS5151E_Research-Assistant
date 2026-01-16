#!/usr/bin/env python3
"""
Rebuild RAG index from scratch.

This script:
1. Clears existing Weaviate index (if present)
2. Reloads documents from data/raw/
3. Chunks and embeds them
4. Writes to Weaviate

Usage:
    python scripts/rebuild_rag_index.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.pipeline import RAGPipeline
from src.utils.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main execution."""
    print("=" * 70)
    print("RAG INDEX REBUILD")
    print("=" * 70)
    
    cfg = load_config()
    
    print(f"\n📍 Configuration:")
    print(f"   Weaviate URL: {cfg.weaviate.url}")
    print(f"   Index name: {cfg.weaviate.index_name}")
    print(f"   Embedding model: {cfg.weaviate.embedding_model}")
    print(f"   Chunk size: {cfg.rag.chunk_size}")
    print(f"   Chunk overlap: {cfg.rag.chunk_overlap}")
    
    # Check data directory
    data_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
    pdfs = list(data_dir.glob("*.pdf"))
    txts = list(data_dir.glob("*.txt"))
    doc_count = len(pdfs) + len(txts)
    
    if doc_count == 0:
        print(f"\n❌ No documents found in {data_dir}")
        print("   Add some .pdf or .txt files and try again.")
        sys.exit(1)
    
    print(f"\n📄 Found {doc_count} documents:")
    for p in pdfs:
        print(f"   - {p.name}")
    for t in txts:
        print(f"   - {t.name}")
    
    print("\n🔄 Rebuilding index...")
    print("   (This may take a minute depending on document count)")
    
    try:
        # This will rebuild the entire index
        pipeline = RAGPipeline.from_config()
        
        print("\n✅ Index rebuilt successfully!")
        print(f"   Weaviate store: {cfg.weaviate.url}")
        print(f"   Index name: {cfg.weaviate.index_name}")
        
        # Quick test retrieval
        print("\n🧪 Testing retrieval...")
        test_docs = pipeline.run(query="artificial intelligence", top_k=3)
        print(f"   Retrieved {len(test_docs)} documents")
        
        if test_docs:
            print("\n   Sample result:")
            sample = test_docs[0]
            content_preview = sample.content[:150].replace("\n", " ")
            print(f"   {content_preview}...")
        
        print("\n" + "=" * 70)
        print("✅ REBUILD COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        logger.exception("Failed to rebuild index")
        print(f"\n❌ Rebuild failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()