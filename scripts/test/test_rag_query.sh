#!/bin/bash
# Quick smoke test for RAG query endpoint
# Requires: curl, jq

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "=========================================="
echo "RAG Query Endpoint - Smoke Test"
echo "=========================================="
echo ""
echo "API URL: ${API_URL}"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ Required command '$1' not found${NC}"
        echo "   Install it and try again."
        exit 1
    fi
}

# Check dependencies
check_command curl
check_command jq

# Test 1: Health check
echo "1️⃣  Testing /health endpoint..."
HEALTH_RESPONSE=$(curl -fsS "${API_URL}/health" 2>&1)
HEALTH_STATUS=$?

if [ $HEALTH_STATUS -eq 0 ]; then
    echo "$HEALTH_RESPONSE" | jq '.'
    echo -e "${GREEN}✅ API is healthy${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
    echo "$HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Test 2: Readiness check
echo "2️⃣  Testing /ready endpoint (Weaviate + Ollama)..."
READY_RESPONSE=$(curl -fsS "${API_URL}/ready" 2>&1)
READY_STATUS=$?

if [ $READY_STATUS -eq 0 ]; then
    echo "$READY_RESPONSE" | jq '.'
    
    WEAVIATE_OK=$(echo "$READY_RESPONSE" | jq -r '.weaviate_ok')
    OLLAMA_OK=$(echo "$READY_RESPONSE" | jq -r '.ollama_ok')
    
    if [ "$WEAVIATE_OK" = "true" ]; then
        echo -e "${GREEN}✅ Weaviate is ready${NC}"
    else
        echo -e "${RED}❌ Weaviate is not ready${NC}"
        exit 1
    fi
    
    if [ "$OLLAMA_OK" = "true" ]; then
        echo -e "${GREEN}✅ Ollama is ready${NC}"
    elif [ "$OLLAMA_OK" = "null" ]; then
        echo -e "${YELLOW}⚠️  Ollama status: not configured${NC}"
    else
        echo -e "${RED}❌ Ollama is not ready${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Readiness check failed${NC}"
    echo "$READY_RESPONSE"
    exit 1
fi
echo ""

# Test 3: RAG query
echo "3️⃣  Testing /rag/query endpoint..."
echo "   Query: 'What is digital transformation?'"
echo "   (This may take 10-30 seconds as it calls the LLM)"
echo ""

PAYLOAD='{
  "query": "What is digital transformation?",
  "language": "en"
}'

RAG_RESPONSE=$(curl -fsS -X POST "${API_URL}/rag/query" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" 2>&1)
RAG_STATUS=$?

if [ $RAG_STATUS -eq 0 ]; then
    echo "$RAG_RESPONSE" | jq '.'
    echo ""
    
    ANSWER=$(echo "$RAG_RESPONSE" | jq -r '.answer')
    
    if [ -n "$ANSWER" ] && [ "$ANSWER" != "null" ] && [ "$ANSWER" != "" ]; then
        echo -e "${GREEN}✅ RAG query successful!${NC}"
        echo ""
        echo "Answer preview (first 300 chars):"
        echo "-----------------------------------"
        echo "$ANSWER" | head -c 300
        echo "..."
        echo "-----------------------------------"
    else
        echo -e "${RED}❌ RAG query returned empty answer${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ RAG query failed${NC}"
    echo "$RAG_RESPONSE"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
echo "=========================================="