#!/bin/bash
# Manual API testing script
# Usage: ./test_api_call.sh [endpoint]

set -e

API_URL="${API_URL:-http://localhost:8000}"
ENDPOINT="${1:-health}"

echo "========================================"
echo "API Testing Script"
echo "========================================"
echo "API URL: $API_URL"
echo "Endpoint: $ENDPOINT"
echo "========================================"
echo ""

case "$ENDPOINT" in
  health)
    echo "Testing /health"
    curl -s "$API_URL/health" | jq
    ;;
  
  ready)
    echo "Testing /ready"
    curl -s "$API_URL/ready" | jq
    ;;
  
  version)
    echo "Testing /version"
    curl -s "$API_URL/version" | jq
    ;;
  
  stats)
    echo "Testing /rag/stats"
    curl -s "$API_URL/rag/stats" | jq
    ;;
  
  ollama)
    echo "Testing /ollama/info"
    curl -s "$API_URL/ollama/info" | jq
    ;;
  
  query)
    echo "Testing /rag/query"
    echo "Query: What is machine learning?"
    curl -s -X POST "$API_URL/rag/query" \
      -H "Content-Type: application/json" \
      -d '{
        "query": "What is machine learning?",
        "language": "en"
      }' | jq '.answer' -r
    ;;
  
  ingest-local)
    echo "Testing /rag/ingest/local"
    curl -s -X POST "$API_URL/rag/ingest/local" \
      -H "Content-Type: application/json" \
      -d '{"pattern": "*"}' | jq
    ;;
  
  ingest-arxiv)
    echo "Testing /rag/ingest/arxiv"
    echo "Query: machine learning, Max: 2"
    curl -s -X POST "$API_URL/rag/ingest/arxiv" \
      -H "Content-Type: application/json" \
      -d '{
        "query": "machine learning",
        "max_results": 2
      }' | jq
    ;;
  
  all)
    echo "Running all tests..."
    echo ""
    
    for test in health ready version stats ollama; do
      echo "--- Testing $test ---"
      $0 $test
      echo ""
      sleep 1
    done
    ;;
  
  *)
    echo "Unknown endpoint: $ENDPOINT"
    echo ""
    echo "Available endpoints:"
    echo "  health          - Health check"
    echo "  ready           - Readiness check"
    echo "  version         - Version info"
    echo "  stats           - RAG statistics"
    echo "  ollama          - Ollama info"
    echo "  query           - Test query"
    echo "  ingest-local    - Test local ingestion"
    echo "  ingest-arxiv    - Test ArXiv ingestion"
    echo "  all             - Run all tests"
    echo ""
    echo "Usage: $0 [endpoint]"
    exit 1
    ;;
esac

echo ""
echo "========================================"
echo "Test complete"
echo "========================================"