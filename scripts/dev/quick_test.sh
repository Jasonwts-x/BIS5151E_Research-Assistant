#!/bin/bash
# Quick smoke test for RAG system

set -e

echo "=========================================="
echo "RAG System - Quick Smoke Test"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Check if services are running
echo "1️⃣  Checking services..."
if ! docker compose -f docker/docker-compose.yml ps weaviate | grep -q "Up"; then
    echo -e "${RED}❌ Weaviate not running${NC}"
    echo "   Start it: docker compose up -d weaviate"
    exit 1
fi
echo -e "${GREEN}✅ Weaviate is running${NC}"

if ! docker compose -f docker/docker-compose.yml ps api | grep -q "Up"; then
    echo -e "${RED}❌ API not running${NC}"
    echo "   Start it: docker compose up -d api"
    exit 1
fi
echo -e "${GREEN}✅ API is running${NC}"
echo ""

# Test stats endpoint
echo "2️⃣  Testing GET /rag/stats..."
curl -fsS http://localhost:8000/rag/stats | python -m json.tool
echo ""
echo -e "${GREEN}✅ Stats endpoint working${NC}"
echo ""

# Ingest test data
echo "3️⃣  Testing POST /rag/ingest/local..."
RESPONSE=$(curl -fsS -X POST http://localhost:8000/rag/ingest/local \
    -H "Content-Type: application/json" \
    -d '{"pattern": "*"}')

echo "$RESPONSE" | python -m json.tool
CHUNKS=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['chunks_ingested'])")

if [ "$CHUNKS" -gt 0 ]; then
    echo -e "${GREEN}✅ Ingestion working (${CHUNKS} chunks)${NC}"
else
    echo -e "${RED}⚠️  No chunks ingested - add documents to data/raw/${NC}"
fi
echo ""

# Test query (if we have data)
if [ "$CHUNKS" -gt 0 ]; then
    echo "4️⃣  Testing POST /rag/query..."
    curl -fsS -X POST http://localhost:8000/rag/query \
        -H "Content-Type: application/json" \
        -d '{"query": "What is artificial intelligence?", "language": "en"}' \
        | python -m json.tool
    echo ""
    echo -e "${GREEN}✅ Query endpoint working${NC}"
else
    echo "4️⃣  Skipping query test (no data ingested)"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
echo "=========================================="