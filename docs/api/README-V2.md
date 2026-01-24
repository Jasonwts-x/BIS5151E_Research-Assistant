# API Reference

Complete API documentation for ResearchAssistantGPT.

---

## 📚 API Overview

**Base URL:** `http://localhost:8000`

**Interactive Docs:** http://localhost:8000/docs (Swagger UI)

**Alternative Docs:** http://localhost:8000/redoc (ReDoc)

---

## 🔌 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |
| `/rag/ingest/arxiv` | POST | Ingest papers from ArXiv |
| `/rag/ingest/local` | POST | Ingest local documents |
| `/rag/query` | POST | Query with multi-agent processing |
| `/rag/stats` | GET | Index statistics |
| `/rag/reset` | POST | Reset vector database |

---

## Health Endpoints

### GET /health

Check if API is running.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-24T10:30:00Z"
}
```

---

### GET /ready

Check if all dependencies are ready.

**Request:**
```bash
curl http://localhost:8000/ready
```

**Response:**
```json
{
  "status": "ready",
  "services": {
    "weaviate": "connected",
    "ollama": "connected"
  }
}
```

---

## Ingestion Endpoints

### POST /rag/ingest/arxiv

Fetch and ingest papers from ArXiv.

**Request Body:**
```json
{
  "query": "machine learning",
  "max_results": 5
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | ✅ | ArXiv search query |
| `max_results` | integer | ❌ | Number of papers (default: 10, max: 20) |

**Example:**
```bash
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{
    "query": "retrieval augmented generation",
    "max_results": 5
  }'
```

**Response:**
```json
{
  "source": "arxiv",
  "documents_loaded": 5,
  "chunks_created": 237,
  "chunks_ingested": 237,
  "chunks_skipped": 0,
  "errors": [],
  "success": true
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Data source ("arxiv") |
| `documents_loaded` | integer | Number of papers downloaded |
| `chunks_created` | integer | Total chunks generated |
| `chunks_ingested` | integer | Chunks added to database |
| `chunks_skipped` | integer | Duplicate chunks skipped |
| `errors` | array | List of errors (if any) |
| `success` | boolean | Overall success status |

**Notes:**
- Takes 30-60 seconds for 5 papers
- Downloads PDFs to `data/arxiv/`
- Extracts metadata (title, authors, abstract, date)
- Idempotent: re-ingesting same papers skips duplicates

---

### POST /rag/ingest/local

Ingest documents from local filesystem.

**Request Body:**
```json
{
  "pattern": "*.pdf"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pattern` | string | ❌ | Glob pattern (default: "*") |

**Example:**
```bash
# Ingest all PDFs
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*.pdf"}'

# Ingest specific files
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "paper-*.pdf"}'
```

**Response:**
```json
{
  "source": "local",
  "documents_loaded": 3,
  "chunks_created": 142,
  "chunks_ingested": 142,
  "chunks_skipped": 0,
  "errors": [],
  "success": true
}
```

**Notes:**
- Reads from `data/raw/` directory
- Supports: PDF, TXT files
- Idempotent: duplicates are skipped

---

## Query Endpoint

### POST /rag/query

Query the system with multi-agent processing.

**Request Body:**
```json
{
  "query": "What is machine learning?",
  "language": "en",
  "top_k": 5
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | ✅ | - | Research question (max 10,000 chars) |
| `language` | string | ❌ | "en" | Target language: en, de, fr, es |
| `top_k` | integer | ❌ | 5 | Number of chunks to retrieve |

**Example:**
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain transformer architecture",
    "language": "en",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "query": "Explain transformer architecture",
  "answer": "The Transformer architecture is a neural network design introduced in 2017...[1][2][3]",
  "source_documents": [
    {
      "content": "The Transformer model...",
      "source": "arxiv-2301.12345-attention-is-all-you-need.pdf",
      "chunk_index": 5,
      "score": 0.92
    }
  ],
  "language": "en"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Original query |
| `answer` | string | Generated summary with citations |
| `source_documents` | array | Retrieved documents with metadata |
| `language` | string | Response language |

**Source Document Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Document chunk text |
| `source` | string | Source filename |
| `chunk_index` | integer | Chunk position in document |
| `score` | float | Relevance score (0-1) |

**Notes:**
- Takes 10-30 seconds depending on query complexity
- Answer includes inline citations [1], [2], etc.
- Citations correspond to source_documents array indices

---

## Statistics Endpoint

### GET /rag/stats

Get index statistics.

**Request:**
```bash
curl http://localhost:8000/rag/stats
```

**Response:**
```json
{
  "total_documents": 15,
  "total_chunks": 742,
  "total_embeddings": 742,
  "vector_dimensions": 384,
  "index_size_mb": 12.4,
  "sources": {
    "arxiv": 10,
    "local": 5
  }
}
```

---

## Admin Endpoints

### POST /rag/reset

Reset vector database (⚠️ deletes all data).

**Request:**
```bash
curl -X POST http://localhost:8000/rag/reset \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

**Response:**
```json
{
  "status": "success",
  "message": "Index reset successfully",
  "chunks_deleted": 742
}
```

---

## Error Responses

### Standard Error Format
```json
{
  "detail": "Error message here"
}
```

### Common Error Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 400 | Bad Request | Invalid input, missing required fields |
| 404 | Not Found | Endpoint doesn't exist |
| 422 | Validation Error | Invalid data type or format |
| 500 | Internal Server Error | Service failure, database error |
| 503 | Service Unavailable | Dependency not ready (Weaviate, Ollama) |

### Error Examples

**Invalid query (too short):**
```json
{
  "detail": "Query must be at least 3 characters"
}
```

**Service unavailable:**
```json
{
  "detail": "Weaviate service not available"
}
```

**Validation error:**
```json
{
  "detail": [
    {
      "loc": ["body", "max_results"],
      "msg": "ensure this value is less than or equal to 20",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## Rate Limits

**Current limits:**
- No rate limiting implemented yet
- Consider ~10 requests/minute for ingestion
- Unlimited queries (but each takes 10-30s)

**Future:** Will add rate limiting in production deployment.

---

## Authentication

**Current status:** No authentication

**Future:** Will add JWT-based authentication for production.

---

## Code Examples

### Python
```python
import requests

# Ingest papers
response = requests.post(
    "http://localhost:8000/rag/ingest/arxiv",
    json={
        "query": "deep learning",
        "max_results": 5
    }
)
print(response.json())

# Query
response = requests.post(
    "http://localhost:8000/rag/query",
    json={
        "query": "What is deep learning?",
        "language": "en"
    }
)
print(response.json()["answer"])
```

### JavaScript
```javascript
// Ingest papers
const ingestResponse = await fetch('http://localhost:8000/rag/ingest/arxiv', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'neural networks',
    max_results: 5
  })
});
const ingestData = await ingestResponse.json();
console.log(ingestData);

// Query
const queryResponse = await fetch('http://localhost:8000/rag/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Explain neural networks',
    language: 'en'
  })
});
const queryData = await queryResponse.json();
console.log(queryData.answer);
```

### cURL
```bash
# Ingest
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "AI ethics", "max_results": 3}'

# Query
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are AI ethics concerns?", "language": "en"}'
```

---

## Webhooks (n8n Integration)

### Trigger Ingestion from n8n

**Workflow node:**
```json
{
  "method": "POST",
  "url": "http://api:8000/rag/ingest/arxiv",
  "body": {
    "query": "{{$json.search_term}}",
    "max_results": 5
  }
}
```

### Query from n8n
```json
{
  "method": "POST",
  "url": "http://api:8000/rag/query",
  "body": {
    "query": "{{$json.question}}",
    "language": "en"
  }
}
```

---

## Best Practices

### Ingestion
- ✅ Start with small batches (3-5 papers)
- ✅ Wait for ingestion to complete before querying
- ✅ Use specific queries for ArXiv (not "AI" or "ML")
- ❌ Don't ingest >20 papers at once

### Querying
- ✅ Ask specific questions
- ✅ Use natural language
- ✅ Reference the topic in your query
- ❌ Don't use single-word queries

### Error Handling
- ✅ Check response status codes
- ✅ Implement retry logic with backoff
- ✅ Log errors for debugging
- ❌ Don't ignore 5xx errors

---

## OpenAPI Specification

Download the full OpenAPI spec:
```bash
curl http://localhost:8000/openapi.json > api-spec.json
```

Use with code generators:
```bash
# Generate Python client
openapi-generator generate -i api-spec.json -g python -o ./client

# Generate TypeScript client
openapi-generator generate -i api-spec.json -g typescript-axios -o ./client
```

---

## Next Steps

- 🔧 [Usage Examples](../examples/README.md) - Code examples
- 🏗️ [Architecture](../architecture/README.md) - How it works
- 🐛 [Troubleshooting](../troubleshooting/README.md) - Common issues

---

**[⬅ Back to Main README](../../README.md)**