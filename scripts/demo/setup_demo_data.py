#!/usr/bin/env python3
"""
Setup Demo Data

Populates the RAG system with sample documents for demonstration.

Usage:
    python scripts/demo/setup_demo_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.rag.core import RAGPipeline

print("=" * 70)
print("SETUP DEMO DATA")
print("=" * 70)
print()

# Ingest local files
print("1. Ingesting local files from data/raw/...")
RAGPipeline.build_index_from_local()

print()
print("2. Fetching sample papers from ArXiv...")
RAGPipeline.build_index_from_arxiv(
    query="retrieval augmented generation",
    max_results=3,
)

print()
print("=" * 70)
print("✅ DEMO DATA SETUP COMPLETE")
print("=" * 70)
print()
print("Try a query:")
print("  python -m src.rag.cli query 'What is RAG?'")
print()
print("Or start the API:")
print("  docker compose up api")
print("  curl -X POST http://localhost:8000/rag/query \\")
print("    -H 'Content-Type: application/json' \\")
print("    -d '{\"query\": \"What is RAG?\", \"language\": \"en\"}'")