# API Usage Examples

Comprehensive examples for REST API endpoints.

## Table of Contents

1. [System Endpoints](#system-endpoints)
2. [RAG Endpoints](#rag-endpoints)
3. [Ollama Endpoints](#ollama-endpoints)
4. [CrewAI Endpoints](#crewai-endpoints)
5. [Error Handling](#error-handling)

---

## System Endpoints

### Health Check

**Simple health check**:
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{"status": "ok"}
```

---

### Readiness Check

**Check all services**:
```bash
curl http://localhost:8000/ready
```

**Response** (healthy):
```json
{
  "status": "ok",
  "weaviate_ok": true,
  "ollama_ok": true
}
```

**Response** (degraded):
```json
{
  "status": "degraded",
  "weaviate_ok": false,
  "ollama_ok": true
}
```

---

### Version Info
```bash
curl http://localhost:8000/version
```

**Response**:
```json
{
  "service": "research-assistant-api",
  "api_version": "0.2.0",
  "python_version": "3.11.7"
}
```

---

## RAG Endpoints

### Query with Summary

**Basic query**:
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is artificial intelligence?",
    "language": "en"
  }'
```

**Response**:
```json
{
  "query": "What is artificial intelligence?",
  "language": "en",
  "answer": "Artificial intelligence (AI) is a field of computer science focused on creating systems capable of performing tasks that typically require human intelligence [1]. These systems include machine learning models that can learn from data and make predictions [2]...",
  "timings": {}
}
```

---

### Ingest Local Files

**Ingest all files**:
```bash
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*"}'
```

**Ingest only PDFs**:
```bash
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*.pdf"}'
```

**Ingest ArXiv papers only**:
```bash
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "arxiv-*.pdf"}'
```

**Response**:
```json
{
  "source": "LocalFiles(data/raw)",
  "documents_loaded": 3,
  "chunks_created": 24,
  "chunks_ingested": 24,
  "chunks_skipped": 0,
  "errors": [],
  "success": true
}
```

---

### Ingest ArXiv Papers

**Basic ingestion**:
```bash
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "max_results": 5
  }'
```

**Advanced search**:
```bash
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ti:\"neural networks\" AND cat:cs.AI",
    "max_results": 10
  }'
```

**Response**:
```json
{
  "source": "ArXiv",
  "documents_loaded": 5,
  "chunks_created": 127,
  "chunks_ingested": 127,
  "chunks_skipped": 0,
  "errors": [],
  "success": true
}
```

---

### Get Index Statistics
```bash
curl http://localhost:8000/rag/stats
```

**Response**:
```json
{
  "collection_name": "ResearchDocument",
  "schema_version": "1.0.0",
  "document_count": 127,
  "exists": true
}
```

---

### Reset Index (Dangerous!)
```bash
curl -X DELETE http://localhost:8000/rag/admin/reset-index
```

**Response**:
```json
{
  "success": true,
  "message": "Index cleared successfully. 127 documents deleted.",
  "previous_document_count": 127
}
```

---

## Ollama Endpoints

### Get Ollama Info
```bash
curl http://localhost:8000/ollama/info
```

**Response**:
```json
{
  "status": "healthy",
  "host": "http://ollama:11434",
  "configured_model": "qwen2.5:3b",
  "available_models": [
    "qwen2.5:3b",
    "qwen3:4b",
    "tinyllama:1.1b"
  ]
}
```

---

### List Models
```bash
curl http://localhost:8000/ollama/models
```

**Response**:
```json
{
  "models": [
    {
      "name": "qwen2.5:3b",
      "size": 1870000000,
      "digest": "sha256:abc123...",
      "modified_at": "2025-01-15T10:30:00Z",
      "details": {}
    }
  ]
}
```

---

### Direct Chat (Low-Level)
```bash
curl -X POST http://localhost:8000/ollama/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:3b",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7
  }'
```

**Response**:
```json
{
  "model": "qwen2.5:3b",
  "message": {
    "role": "assistant",
    "content": "Hello! How can I help you today?"
  },
  "done": true
}
```

---

## CrewAI Endpoints

### Execute Workflow
```bash
curl -X POST http://localhost:8000/crewai/run \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Explain neural networks",
    "language": "en"
  }'
```

**Response**:
```json
{
  "topic": "Explain neural networks",
  "language": "en",
  "answer": "Neural networks are computational models inspired by biological neural networks..."
}
```

---

## Error Handling

### Service Unavailable

**Request**:
```bash
# When Weaviate is down
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "language": "en"}'
```

**Response** (503):
```json
{
  "detail": "CrewAI service unavailable: Connection refused"
}
```

---

### Bad Request

**Request**:
```bash
# Empty query
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "", "language": "en"}'
```

**Response** (422):
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "query"],
      "msg": "String should have at least 1 character"
    }
  ]
}
```

---

### Collection Not Found

**Request**:
```bash
# Before ingesting any documents
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "language": "en"}'
```

**Response** (500):
```json
{
  "detail": "Collection 'ResearchDocument' does not exist in Weaviate!"
}
```

**Solution**: Ingest documents first

---

## Advanced Usage

### Pipeline with jq

**Extract only the answer**:
```bash
curl -s -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?", "language": "en"}' \
  | jq -r '.answer'
```

**Save to file**:
```bash
curl -s -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?", "language": "en"}' \
  | jq -r '.answer' > summary.txt
```

---

### Batch Processing
```bash
#!/bin/bash
# Process multiple queries

queries=(
  "What is machine learning?"
  "Explain neural networks"
  "What is deep learning?"
)

for query in "${queries[@]}"; do
  echo "Query: $query"
  
  curl -s -X POST http://localhost:8000/rag/query \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$query\", \"language\": \"en\"}" \
    | jq -r '.answer' > "${query// /_}.txt"
  
  echo "Saved to ${query// /_}.txt"
  echo "---"
done
```

---

### Error Handling in Scripts
```bash
#!/bin/bash
# Robust error handling

response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?", "language": "en"}')

# Extract status code
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
  echo "Success!"
  echo "$body" | jq -r '.answer'
else
  echo "Error: HTTP $http_code"
  echo "$body" | jq -r '.detail'
  exit 1
fi
```

---

## Performance Tips

### 1. Reduce Response Time

**Use smaller top_k** (not configurable via API yet):
- Contact admin to adjust RAG_TOP_K in .env

**Use smaller model**:
```bash
# Configure LLM_MODEL=tinyllama:1.1b in .env for faster (but lower quality) responses
```

---

### 2. Batch Ingestion

**Ingest multiple sources**:
```bash
# Ingest local files
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*"}'

# Then ArXiv
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "topic", "max_results": 10}'
```

---

### 3. Monitor Progress

**Check stats periodically**:
```bash
watch -n 5 'curl -s http://localhost:8000/rag/stats | jq'
```

---

## Testing

### Quick Smoke Test
```bash
#!/bin/bash
# Test all endpoints

echo "Testing /health"
curl -s http://localhost:8000/health | jq

echo "Testing /ready"
curl -s http://localhost:8000/ready | jq

echo "Testing /version"
curl -s http://localhost:8000/version | jq

echo "Testing /ollama/info"
curl -s http://localhost:8000/ollama/info | jq

echo "Testing /rag/stats"
curl -s http://localhost:8000/rag/stats | jq

echo "All tests complete!"
```

---

**[⬆ Back to Examples](README.md)**