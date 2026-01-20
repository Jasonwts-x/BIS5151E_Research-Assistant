#!/usr/bin/env python3
"""
Verify Determinism

Tests that rebuilding the index produces identical chunk IDs.

Usage:
    python scripts/demo/verify_determinism.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.rag.ingestion import IngestionEngine
from src.rag.sources import LocalFileSource

print("=" * 70)
print("DETERMINISM VERIFICATION TEST")
print("=" * 70)
print()
print("This test verifies that re-ingesting the same documents")
print("produces identical chunk IDs (content-hash based).")
print()

# Setup
data_dir = ROOT / "data" / "raw"
engine = IngestionEngine()

# Check if we have any documents
source = LocalFileSource(data_dir)
try:
    test_fetch = source.fetch(pattern="*")
    if not test_fetch:
        print("❌ No documents found in data/raw/")
        print("   Add some test documents first:")
        print("   - Copy a PDF or TXT file to data/raw/")
        print("   - Or run: python -m src.rag.cli ingest-arxiv 'test query' --max-results 1")
        sys.exit(1)
    
    doc_count = len(test_fetch)
    print(f"✓ Found {doc_count} documents to test with")
    print()
    
except Exception as e:
    print(f"❌ Failed to access documents: {e}")
    sys.exit(1)

# Test 1: Fresh ingestion
print("Test 1: Fresh ingestion")
print("-" * 70)
print("Clearing index...")
engine.clear_index()

print("Ingesting documents (first time)...")
result1 = engine.ingest_from_source(source)

print(f"✓ Ingested: {result1.chunks_ingested} chunks")
print(f"✓ Skipped: {result1.chunks_skipped} chunks")
print()

if result1.chunks_ingested == 0:
    print("❌ No chunks were ingested - something is wrong")
    sys.exit(1)

# Test 2: Re-ingest same documents (should skip all)
print("Test 2: Re-ingestion (determinism check)")
print("-" * 70)
print("Re-ingesting same documents...")
result2 = engine.ingest_from_source(source)

print(f"✓ Ingested: {result2.chunks_ingested} chunks (should be 0)")
print(f"✓ Skipped: {result2.chunks_skipped} chunks (should equal first ingestion)")
print()

# Verify
if result2.chunks_skipped == result1.chunks_ingested:
    print("=" * 70)
    print("✅ DETERMINISM TEST PASSED")
    print("=" * 70)
    print()
    print(f"Re-ingesting {result1.chunks_ingested} chunks resulted in:")
    print(f"  - 0 new chunks ingested (expected)")
    print(f"  - {result2.chunks_skipped} duplicates skipped (expected)")
    print()
    print("This proves that content-hash IDs are deterministic:")
    print("  Same content → Same ID → Automatic deduplication ✓")
    sys.exit(0)
else:
    print("=" * 70)
    print("❌ DETERMINISM TEST FAILED")
    print("=" * 70)
    print()
    print("Expected:")
    print(f"  - All {result1.chunks_ingested} chunks to be skipped as duplicates")
    print()
    print("Got:")
    print(f"  - {result2.chunks_ingested} new chunks ingested (should be 0)")
    print(f"  - {result2.chunks_skipped} chunks skipped (should be {result1.chunks_ingested})")
    print()
    print("This indicates chunk IDs are NOT deterministic!")
    sys.exit(1)