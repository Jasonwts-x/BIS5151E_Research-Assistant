# API Documentation

Complete REST API reference for ResearchAssistantGPT.

## Base URL
```
http://localhost:8000
```

## Interactive Documentation

**Swagger UI**: http://localhost:8000/docs  
**ReDoc**: http://localhost:8000/redoc

---

## Table of Contents

1. [Authentication](#authentication)
2. [System Endpoints](#system-endpoints)
3. [RAG Endpoints](#rag-endpoints)
4. [Ollama Endpoints](#ollama-endpoints)
5. [CrewAI Endpoints](#crewai-endpoints)
6. [Error Handling](#error-handling)
7. [Rate Limits](#rate-limits)

---

## Authentication

**Current Version**: No authentication required (local development)

**Future**: JWT tokens or API keys for production deployment.

---

## System Endpoints

### GET /health

**Description**: Liveness check - confirms API is responsive.

**Response**:
```json
{
  "status": "ok"
}
```

**Example**:
```bash
curl http://localhost:8000/health
```

---

### GET /version

**Description**: Service version and runtime information.

**Response**:
```json
{
  "service": "research-assistant-api",
  "api_version": "0.2.0",
  "python_version": "3.11.7"
}
```

---

### GET /ready

**Description**: Readiness check - verifies all dependent services are available.

**Response**:
```json
{
  "status": "ok",
  "weaviate_ok": true,
  "ollama_ok": true
}
```

**Status Values**:
- `ok`: All services healthy
- `degraded`: Some services unavailable

---

## RAG Endpoints

### POST /rag/query

**Description**: Execute full RAG pipeline with multi-agent processing.

**Request Body**:
```json
{
  "query": "What is machine learning?",
  "language": "en"
}
```

**Parameters**:
- `query` (string, required): Research question or topic
- `language` (string, optional): Output language. Default: "en"
  - Supported: "en", "de", "fr", "es"

**Response**:
```json
{
  "query": "What is machine learning?",
  "language": "en",
  "answer": "Machine learning is a method of data analysis that automates analytical model building [1]. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention [2]...",
  "timings": {}
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain neural networks",
    "language": "en"
  }'
```

**Notes**:
- Takes 10-60 seconds depending on model and query complexity
- Answer includes inline citations [1], [2], etc.
- Sources are verified by FactChecker agent

---

### POST /rag/ingest/local

**Description**: Ingest documents from local filesystem (data/raw/).

**Request Body**:
```json
{
  "pattern": "*"
}
```

**Parameters**:
- `pattern` (string, optional): File glob pattern. Default: "*"
  - Examples: "*.pdf", "arxiv*", "paper_2024_*.txt"

**Response**:
```json
{
  "source": "LocalFiles(data/raw)",
  "documents_loaded": 5,
  "chunks_created": 42,
  "chunks_ingested": 42,
  "chunks_skipped": 0,
  "errors": [],
  "success": true
}
```

**Example**:
```bash
# Ingest all files
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*"}'

# Ingest only PDFs
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*.pdf"}'
```

**Notes**:
- Idempotent: Re-ingesting same files skips duplicates
- Supported formats: PDF, TXT
- Files must be in `data/raw/` directory

---

### POST /rag/ingest/arxiv

**Description**: Fetch and ingest papers from ArXiv.

**Request Body**:
```json
{
  "query": "machine learning",
  "max_results": 5
}
```

**Parameters**:
- `query` (string, required): ArXiv search query
- `max_results` (integer, optional): Number of papers to fetch. Range: 1-20. Default: 5

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

**Example**:
```bash
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{
    "query": "retrieval augmented generation",
    "max_results": 10
  }'
```

**Notes**:
- Downloads PDFs to `data/raw/`
- Extracts metadata (authors, abstract, categories)
- May take 30-90 seconds for large result sets
- Idempotent: Re-fetching same papers skips duplicates

---

### GET /rag/stats

**Description**: Get RAG index statistics.

**Response**:
```json
{
  "collection_name": "ResearchDocument",
  "schema_version": "1.0.0",
  "document_count": 127,
  "exists": true
}
```

**Example**:
```bash
curl http://localhost:8000/rag/stats
```

---

### DELETE /rag/admin/reset-index

**Description**: Clear all documents from index.

⚠️ **Warning**: This is DESTRUCTIVE and deletes all data!

**Response**:
```json
{
  "success": true,
  "message": "Index cleared successfully. 127 documents deleted.",
  "previous_document_count": 127
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8000/rag/admin/reset-index
```

**Use Cases**:
- Reset after schema changes
- Clean up test data
- Start fresh with new documents

---

## Ollama Endpoints

### GET /ollama/info

**Description**: Get Ollama service status and available models.

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

### GET /ollama/models

**Description**: List all Ollama models with details.

**Response**:
```json
{
  "models": [
    {
      "name": "qwen2.5:3b",
      "size": 1870000000,
      "digest": "abc123...",
      "modified_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

### POST /ollama/chat

**Description**: Direct chat completion (low-level LLM access).

**Note**: For production use, prefer `/rag/query` which includes RAG and multi-agent processing.

**Request Body**:
```json
{
  "model": "qwen2.5:3b",
  "messages": [
    {
      "role": "user",
      "content": "Hello!"
    }
  ],
  "temperature": 0.7
}
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

### POST /crewai/run

**Description**: Execute CrewAI multi-agent workflow directly.

**Note**: This is a low-level endpoint. For typical use, prefer `/rag/query` which handles everything.

**Request Body**:
```json
{
  "topic": "Explain machine learning",
  "language": "en"
}
```

**Response**:
```json
{
  "topic": "Explain machine learning",
  "language": "en",
  "answer": "Machine learning is..."
}
```

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Dependent service (Weaviate, Ollama) down |

### Common Errors

**1. Service Unavailable (503)**
```json
{
  "detail": "Weaviate service unavailable"
}
```
**Solution**: Check service health with `/ready`

**2. Collection Does Not Exist**
```json
{
  "detail": "Collection 'ResearchDocument' does not exist in Weaviate!"
}
```
**Solution**: Ingest documents first

**3. ArXiv Ingestion Timeout**
```json
{
  "detail": "ArXiv ingestion failed: Connection timeout"
}
```
**Solution**: Reduce `max_results` or check network connectivity

---

## Rate Limits

**Current Version**: No rate limits (local development)

**Future**: Rate limiting for production deployment.

---

## Advanced Usage

### Pagination

Not currently implemented. All results returned in single response.

### Filtering

Not currently implemented. Future feature.

### Webhooks

Not currently implemented. Use n8n workflows for event-driven architecture.

---

## SDK Examples

### Python
```python
import requests

# Query
response = requests.post(
    "http://localhost:8000/rag/query",
    json={"query": "What is AI?", "language": "en"}
)
result = response.json()
print(result["answer"])

# Ingest ArXiv
response = requests.post(
    "http://localhost:8000/rag/ingest/arxiv",
    json={"query": "neural networks", "max_results": 5}
)
print(f"Ingested {response.json()['chunks_ingested']} chunks")
```

### JavaScript
```javascript
// Query
const response = await fetch('http://localhost:8000/rag/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'What is AI?',
    language: 'en'
  })
});
const result = await response.json();
console.log(result.answer);
```

### cURL

See examples throughout this document.

---

## Testing

**Interactive Testing**: http://localhost:8000/docs

**Automated Testing**:
```bash
# Run API tests
pytest tests/integration/test_api_endpoints.py -v
```

---

## Changelog

See [API Changelog](CHANGELOG.md) for version history.

---

**[⬆ Back to Documentation](../README.md)**