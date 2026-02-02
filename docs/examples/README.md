# Usage Examples

Practical code examples and integration guides.

---

## 📚 Example Documentation

| Document | Description |
|----------|-------------|
| **[BASIC_USAGE.md](BASIC_USAGE.md)** | Simple query examples |
| **[PYTHON_EXAMPLES.md](PYTHON_EXAMPLES.md)** | Python SDK integration |
| **[CLI_EXAMPLES.md](CLI_EXAMPLES.md)** | Command-line tools | # <- Add this

---

## 🚀 Quick Examples

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

# Research query
$body = @{
    query = "What is machine learning?"
    language = "en"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "`nAnswer:"
Write-Host $response.answer
```

### Bash (Linux/macOS)
```bash
# Ingest papers
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning","max_results":3}'

# Research query
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

## 📖 By Use Case

### Academic Research
- [Literature Review](BASIC_USAGE.md#literature-review)
- [Paper Summaries](BASIC_USAGE.md#paper-summaries)
- [Citation Extraction](BASIC_USAGE.md#citation-extraction)

### Automation
- [Daily ArXiv Digest](N8N_WORKFLOWS.md#daily-digest)
- [Scheduled Research](N8N_WORKFLOWS.md#scheduled-research)
- [Email Notifications](N8N_WORKFLOWS.md#email-notifications)

### Integration
- [Python Application](PYTHON_EXAMPLES.md#application-integration)
- [Web Application](PYTHON_EXAMPLES.md#web-integration)
- [REST API Client](ADVANCED_INTEGRATION.md#rest-client)

---

## 🔗 Related Documentation

- **[API Reference](../api/ENDPOINTS.md)** - All endpoints
- **[Setup Guide](../setup/INSTALLATION.md)** - Installation
- **[n8n Setup](../setup/N8N.md)** - Workflow automation

---

**[⬅ Back to Documentation](../README.md)**