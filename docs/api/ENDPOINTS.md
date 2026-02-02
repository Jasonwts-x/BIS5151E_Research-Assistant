# API Endpoints Reference

Complete reference of all API endpoints.

---

## 📋 System Endpoints

| Endpoint | Method | Description | Auth | Rate Limit |
|----------|--------|-------------|------|------------|
| `/health` | GET | Health check (always returns OK) | None | None |
| `/ready` | GET | Readiness check (checks dependencies) | None | None |
| `/version` | GET | API version information | None | None |

### GET /health

**Description**: Simple health check endpoint. Always returns 200 if API is running.

**Request**: None

**Response**: `200 OK`
```json
{
  "status": "healthy"
}
```

**Example**:
```bash
curl http://localhost:8000/health
```

---

### GET /ready

**Description**: Check if API and all dependencies are ready.

**Request**: None

**Response**: `200 OK`
```json
{
  "status": "ok",
  "weaviate_ok": true,
  "ollama_ok": true
}
```

**Response**: `503 Service Unavailable` (if dependencies down)
```json
{
  "status": "unavailable",
  "weaviate_ok": false,
  "ollama_ok": true
}
```

**Example**:
```bash
curl http://localhost:8000/ready
```

---

### GET /version

**Description**: Get API version and build information.

**Request**: None

**Response**: `200 OK`
```json
{
  "version": "1.0.0",
  "build_date": "2025-02-02",
  "python_version": "3.11.0"
}
```

---

## 📥 RAG Ingestion Endpoints

| Endpoint | Method | Description | Auth | Avg Time |
|----------|--------|-------------|------|----------|
| `/rag/ingest/arxiv` | POST | Ingest papers from ArXiv | None | 30-60s |
| `/rag/ingest/local` | POST | Ingest local PDF/TXT files | None | 10-30s |
| `/rag/reset` | POST | Reset index (delete all documents) | None | 1s |

### POST /rag/ingest/arxiv

**Description**: Search ArXiv, download papers, extract text, chunk, embed, and store in Weaviate.

**Request Body**:
```json
{
  "query": "machine learning",
  "max_results": 3
}
```

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| query | string | ✅ Yes | - | ArXiv search query |
| max_results | integer | ❌ No | 10 | Max papers (1-100) |

**Response**: `200 OK`
```json
{
  "source": "arxiv",
  "documents_loaded": 3,
  "chunks_created": 142,
  "chunks_ingested": 142,
  "chunks_skipped": 0,
  "errors": [],
  "success": true,
  "duration_seconds": 45.3
}
```

**Error Responses**:
- `400 Bad Request`: Invalid query or max_results
- `500 Internal Server Error`: ArXiv API error or processing failure

**Example (PowerShell)**:
```powershell
$body = @{
    query = "transformers attention"
    max_results = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Example (Bash)**:
```bash
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query":"transformers attention","max_results":5}'
```

---

### POST /rag/ingest/local

**Description**: Ingest PDF and TXT files from `data/raw/` directory.

**Request Body**:
```json
{
  "pattern": "*"
}
```

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| pattern | string | ❌ No | "*" | Glob pattern (e.g., "*.pdf", "paper*.txt") |

**Response**: `200 OK`
```json
{
  "source": "local",
  "documents_loaded": 5,
  "chunks_created": 234,
  "chunks_ingested": 234,
  "chunks_skipped": 0,
  "errors": [],
  "success": true,
  "duration_seconds": 12.7
}
```

**Error Responses**:
- `400 Bad Request`: Invalid pattern
- `404 Not Found`: No files match pattern
- `500 Internal Server Error`: File processing error

**Example (PowerShell)**:
```powershell
$body = @{
    pattern = "*.pdf"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/local" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

### POST /rag/reset

**Description**: Delete all documents from Weaviate index. **Use with caution!**

**Request Body**:
```json
{
  "confirm": true
}
```

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| confirm | boolean | ✅ Yes | - | Must be `true` to confirm |

**Response**: `200 OK`
```json
{
  "message": "Index reset successfully",
  "documents_deleted": 150
}
```

**Error Responses**:
- `400 Bad Request`: Missing or false confirmation
- `500 Internal Server Error`: Reset failed

**Example (PowerShell)**:
```powershell
$body = @{ confirm = $true } | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/reset" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

## 🔍 RAG Query Endpoints

| Endpoint | Method | Description | Auth | Avg Time |
|----------|--------|-------------|------|----------|
| `/rag/query` | POST | Query documents (RAG only, no agents) | None | 1-2s |
| `/rag/stats` | GET | Get index statistics | None | <100ms |

### POST /rag/query

**Description**: Query documents using hybrid search (BM25 + vector). Returns raw retrieved chunks without agent processing.

**Request Body**:
```json
{
  "query": "What are neural networks?",
  "top_k": 5,
  "language": "en"
}
```

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| query | string | ✅ Yes | - | Search query (max 10,000 chars) |
| top_k | integer | ❌ No | 5 | Number of chunks to retrieve (1-20) |
| language | string | ❌ No | "en" | Response language (en/de/fr/es) |

**Response**: `200 OK`
```json
{
  "query": "What are neural networks?",
  "documents": [
    {
      "content": "Neural networks are computational models...",
      "source": "paper1.pdf",
      "score": 0.89,
      "metadata": {
        "authors": ["Smith, J.", "Doe, A."],
        "publication_date": "2024-01-15"
      }
    },
    {
      "content": "A neural network consists of layers...",
      "source": "paper2.pdf",
      "score": 0.85,
      "metadata": {...}
    }
  ],
  "total_results": 2,
  "retrieval_time": 0.45
}
```

**Error Responses**:
- `400 Bad Request`: Invalid query or parameters
- `404 Not Found`: No documents in index
- `500 Internal Server Error`: Search error

**Example (PowerShell)**:
```powershell
$body = @{
    query = "What are transformers?"
    top_k = 10
    language = "en"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

### GET /rag/stats

**Description**: Get statistics about the document index.

**Request**: None

**Response**: `200 OK`
```json
{
  "total_documents": 15,
  "total_chunks": 642,
  "sources": ["paper1.pdf", "paper2.pdf", ...],
  "index_size_mb": 12.5,
  "last_ingestion": "2025-02-02T10:30:00Z"
}
```

**Example**:
```bash
curl http://localhost:8000/rag/stats
```

---

## 🔬 Research Endpoints

| Endpoint | Method | Description | Auth | Avg Time |
|----------|--------|-------------|------|----------|
| `/research/query` | POST | Complete research workflow (RAG + agents) | None | 25-35s |

### POST /research/query

**Description**: Complete research workflow - retrieves context from Weaviate, runs multi-agent processing (Writer → Reviewer → FactChecker), returns fact-checked summary with citations.

**Request Body**:
```json
{
  "query": "Explain the transformer attention mechanism",
  "language": "en",
  "top_k": 5
}
```

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| query | string | ✅ Yes | - | Research question (max 10,000 chars) |
| language | string | ❌ No | "en" | Response language (en/de/fr/es) |
| top_k | integer | ❌ No | 5 | Context chunks to retrieve (1-20) |

**Response**: `200 OK`
```json
{
  "query": "Explain the transformer attention mechanism",
  "answer": "The transformer attention mechanism enables models to weigh the importance of different input elements [1]. It computes attention scores using query, key, and value matrices [2]. This self-attention allows the model to capture long-range dependencies efficiently [3]...",
  "sources": [
    {
      "index": 1,
      "source": "attention_is_all_you_need.pdf",
      "content": "We propose a new simple network architecture...",
      "authors": ["Vaswani, A.", "et al."],
      "publication_date": "2017-06-12"
    },
    {
      "index": 2,
      "source": "bert_paper.pdf",
      "content": "Attention mechanisms compute...",
      "authors": ["Devlin, J.", "et al."],
      "publication_date": "2018-10-11"
    }
  ],
  "language": "en",
  "processing_time": 28.4,
  "metrics": {
    "retrieval_time": 0.5,
    "writer_time": 10.2,
    "reviewer_time": 5.1,
    "factchecker_time": 10.3
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid query, language, or parameters
- `404 Not Found`: No documents in index
- `500 Internal Server Error`: Agent processing error
- `503 Service Unavailable`: CrewAI or Ollama unavailable

**Example (PowerShell)**:
```powershell
$body = @{
    query = "What are the applications of deep learning in healthcare?"
    language = "en"
    top_k = 10
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Answer:"
Write-Host $response.answer
Write-Host "`nSources: $($response.sources.Count)"
```

---

## 🤖 CrewAI Endpoints (Proxied)

| Endpoint | Method | Description | Auth | Avg Time |
|----------|--------|-------------|------|----------|
| `/crewai/run` | POST | Execute multi-agent workflow | None | 25-30s |
| `/crewai/health` | GET | CrewAI service health | None | <100ms |

### POST /crewai/run

**Description**: Directly execute CrewAI multi-agent workflow. Proxied to CrewAI service.

**Request Body**:
```json
{
  "query": "Explain quantum computing",
  "context": "Quantum computers use qubits...",
  "language": "en"
}
```

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| query | string | ✅ Yes | - | Research question |
| context | string | ✅ Yes | - | Retrieved context for agents |
| language | string | ❌ No | "en" | Response language |

**Response**: `200 OK`
```json
{
  "result": "Quantum computing leverages quantum mechanics...",
  "execution_time": 25.6
}
```

**Error Responses**:
- `400 Bad Request`: Invalid input
- `503 Service Unavailable`: CrewAI service down

---

### GET /crewai/health

**Description**: Check CrewAI service health.

**Response**: `200 OK`
```json
{
  "status": "healthy"
}
```

---

## 🦙 Ollama Endpoints (Proxied)

| Endpoint | Method | Description | Auth | Avg Time |
|----------|--------|-------------|------|----------|
| `/ollama/models` | GET | List available models | None | <100ms |
| `/ollama/chat` | POST | Chat completion | None | 5-15s |
| `/ollama/pull` | POST | Download model | None | 1-10min |
| `/ollama/info` | GET | Get model info | None | <100ms |

### GET /ollama/models

**Description**: List all available Ollama models.

**Response**: `200 OK`
```json
{
  "models": [
    {
      "name": "qwen3:1.7b",
      "size": "1.0 GB",
      "modified": "2025-02-01T12:00:00Z"
    },
    {
      "name": "qwen3:4b",
      "size": "2.4 GB",
      "modified": "2025-02-01T12:05:00Z"
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/ollama/models
```

---

### POST /ollama/chat

**Description**: Get chat completion from Ollama model.

**Request Body**:
```json
{
  "model": "qwen3:1.7b",
  "messages": [
    {
      "role": "user",
      "content": "Explain neural networks in one sentence."
    }
  ],
  "temperature": 0.3,
  "max_tokens": 100
}
```

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| model | string | ✅ Yes | - | Model name (e.g., "qwen3:1.7b") |
| messages | array | ✅ Yes | - | Chat messages |
| temperature | float | ❌ No | 0.3 | Randomness (0.0-1.0) |
| max_tokens | integer | ❌ No | 2048 | Max response tokens |

**Response**: `200 OK`
```json
{
  "model": "qwen3:1.7b",
  "message": {
    "role": "assistant",
    "content": "Neural networks are computational models inspired by biological neurons that learn patterns from data."
  },
  "done": true,
  "total_duration": 5420000000
}
```

**Example (PowerShell)**:
```powershell
$body = @{
    model = "qwen3:1.7b"
    messages = @(
        @{
            role = "user"
            content = "What is machine learning?"
        }
    )
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://localhost:8000/ollama/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

### POST /ollama/pull

**Description**: Download an Ollama model.

**Request Body**:
```json
{
  "name": "qwen3:1.7b"
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "message": "Model pulled successfully"
}
```

**Example (PowerShell)**:
```powershell
$body = @{ name = "llama3.2:3b" } | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/ollama/pull" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

### GET /ollama/info

**Description**: Get information about a specific model.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model | string | ✅ Yes | Model name |

**Response**: `200 OK`
```json
{
  "model": "qwen3:1.7b",
  "size": "1.0 GB",
  "parameters": "1.7B",
  "quantization": "Q4_K_M",
  "family": "qwen"
}
```

**Example**:
```bash
curl "http://localhost:8000/ollama/info?model=qwen3:1.7b"
```

---

## 📊 Response Times Summary

| Endpoint | Typical Time | Notes |
|----------|--------------|-------|
| `/health` | < 10ms | Instant |
| `/ready` | < 100ms | Checks dependencies |
| `/rag/ingest/arxiv` | 30-60s | 3 papers, network dependent |
| `/rag/ingest/local` | 10-30s | Depends on file size |
| `/rag/query` | 0.5-2s | Fast retrieval |
| `/research/query` | 25-35s | Full multi-agent workflow |
| `/crewai/run` | 25-30s | Agent processing |
| `/ollama/chat` | 5-15s | LLM generation |

---

## 🚨 Common Errors

### 400 Bad Request
```json
{
  "detail": "Query exceeds maximum length of 10000 characters"
}
```

**Solutions**:
- Check input validation
- Shorten query
- Verify parameter types

### 404 Not Found
```json
{
  "detail": "No documents found in index. Please ingest documents first."
}
```

**Solutions**:
- Ingest documents using `/rag/ingest/arxiv` or `/rag/ingest/local`
- Check `/rag/stats` to verify documents exist

### 503 Service Unavailable
```json
{
  "detail": "Weaviate service is unavailable"
}
```

**Solutions**:
- Check `/ready` endpoint
- Verify Weaviate is running: `docker compose ps weaviate`
- Restart service: `docker compose restart weaviate`

---

## 📚 Related Documentation

- **[API Overview](README.md)** - API introduction
- **[Schemas](SCHEMAS.md)** - Request/response models
- **[Examples](EXAMPLES.md)** - Integration code
- **[Setup Guide](../setup/INSTALLATION.md)** - Installation

---

**[⬅ Back to API Documentation](README.md)**