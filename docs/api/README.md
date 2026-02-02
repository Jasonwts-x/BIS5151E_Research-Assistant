# API Documentation

Complete REST API reference for ResearchAssistantGPT.

---

## 📚 API Documentation

| Document | Description |
|----------|-------------|
| **[ENDPOINTS.md](ENDPOINTS.md)** | Complete endpoint reference (table) |
| **[SCHEMAS.md](SCHEMAS.md)** | Request/response schemas |
| **[../examples/README.md](../examples/README.md)** | Integration examples |
| **[AUTHENTICATION.md](AUTHENTICATION.md)** | Authentication (future) |

---

## 🚀 Quick Start

### Base URL
```
http://localhost:8000
```

**Production**: Change to your domain

### Interactive Documentation

**Swagger UI**: http://localhost:8000/docs  
**ReDoc**: http://localhost:8000/redoc

---

## 📋 Endpoint Categories

### System Endpoints
Health checks and system information

- `GET /health` - Health check
- `GET /ready` - Readiness check (dependencies)
- `GET /version` - API version

### RAG Endpoints
Document ingestion and retrieval

- `POST /rag/ingest/arxiv` - Ingest from ArXiv
- `POST /rag/ingest/local` - Ingest local files
- `POST /rag/query` - Query documents (RAG only)
- `GET /rag/stats` - Index statistics
- `POST /rag/reset` - Reset index (dev only)

### Research Endpoints
Complete research workflows

- `POST /research/query` - Full workflow (ingest + multi-agent query)
- `POST /research/async` - Async workflow (future)
- `GET /research/status/{job_id}` - Check status (future)

### CrewAI Endpoints
Multi-agent operations (proxied)

- `POST /crewai/run` - Execute multi-agent workflow
- `POST /crewai/async` - Async execution (future)
- `GET /crewai/status/{job_id}` - Check status (future)

### Ollama Endpoints
LLM operations (proxied)

- `GET /ollama/models` - List models
- `POST /ollama/chat` - Chat completion
- `POST /ollama/pull` - Pull model
- `GET /ollama/info` - Model info

---

## 🔑 Authentication

**Current**: None (local deployment)

**Future**: JWT tokens
```http
Authorization: Bearer <token>
```

See [AUTHENTICATION.md](AUTHENTICATION.md) for details.

---

## 📊 Rate Limits

**Current**: None

**Future**: 
- 100 requests/minute per IP
- 1000 requests/hour per user

---

## 🐛 Error Handling

### Error Response Format
```json
{
  "detail": "Error message",
  "status_code": 400,
  "type": "ValidationError"
}
```

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Success |
| 400 | Bad Request | Invalid input |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Dependency down |

---

## 📖 Usage Examples

### PowerShell (Windows)
```powershell
# Ingest papers
$body = @{
    query = "machine learning"
    max_results = 3
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Ingested: $($response.documents_loaded) papers"

# Query
$body = @{
    query = "What is machine learning?"
    language = "en"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host $response.answer
```

### Bash (Linux/macOS)
```bash
# Ingest papers
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning","max_results":3}'

# Query
curl -X POST http://localhost:8000/research/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is machine learning?","language":"en"}'
```

### Python
```python
import requests

# Ingest
response = requests.post(
    "http://localhost:8000/rag/ingest/arxiv",
    json={"query": "machine learning", "max_results": 3}
)
print(f"Ingested: {response.json()['documents_loaded']} papers")

# Query
response = requests.post(
    "http://localhost:8000/research/query",
    json={"query": "What is machine learning?", "language": "en"}
)
print(response.json()["answer"])
```

---

## 🔗 Related Documentation

- **[Complete Endpoint Reference](ENDPOINTS.md)** - All endpoints
- **[Request/Response Schemas](SCHEMAS.md)** - Data models
- **[Code Examples](EXAMPLES.md)** - Integration examples
- **[Setup Guide](../setup/INSTALLATION.md)** - Installation

---

**[⬅ Back to Documentation](../README.md)**