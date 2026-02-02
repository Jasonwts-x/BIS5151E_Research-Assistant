# Basic Usage Examples

Simple examples for common tasks.

---

## 📋 Table of Contents

- [First Query](#first-query)
- [Ingesting Documents](#ingesting-documents)
- [Querying Documents](#querying-documents)
- [Multilingual Queries](#multilingual-queries)
- [Checking Status](#checking-status)

---

## 🚀 First Query

### Complete Workflow (Ingest + Query)

**PowerShell**:
```powershell
# 1. Ingest papers
$body = @{
    query = "neural networks"
    max_results = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# 2. Wait for ingestion to complete (30-60s)
Start-Sleep -Seconds 60

# 3. Query
$body = @{
    query = "What are neural networks?"
    language = "en"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host $response.answer
```

**Bash**:
```bash
# 1. Ingest papers
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query":"neural networks","max_results":3}'

# 2. Wait
sleep 60

# 3. Query
curl -X POST http://localhost:8000/research/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What are neural networks?","language":"en"}'
```

---

## 📥 Ingesting Documents

### From ArXiv

**Simple query**:
```powershell
$body = @{
    query = "machine learning"
    max_results = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Specific topic**:
```powershell
$body = @{
    query = "transformers attention mechanism"
    max_results = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**With error handling**:
```powershell
try {
    $body = @{
        query = "quantum computing"
        max_results = 3
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
    
    Write-Host "✅ Success: Ingested $($response.documents_loaded) papers"
    Write-Host "   Chunks created: $($response.chunks_created)"
    Write-Host "   Duration: $($response.duration_seconds)s"
}
catch {
    Write-Host "❌ Error: $($_.Exception.Message)"
}
```

---

### From Local Files

**Place files in `data/raw/`**:
```bash
# Copy your PDFs
cp /path/to/paper1.pdf data/raw/
cp /path/to/paper2.pdf data/raw/
```

**Ingest all files**:
```powershell
$body = @{
    pattern = "*"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/local" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Ingest only PDFs**:
```powershell
$body = @{
    pattern = "*.pdf"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/local" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Ingest specific files**:
```powershell
$body = @{
    pattern = "paper_2024_*.pdf"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/local" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

## 🔍 Querying Documents

### Simple Query
```powershell
$body = @{
    query = "What is deep learning?"
    language = "en"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host $response.answer
```

---

### Query with More Context

Retrieve more chunks for comprehensive answers:
```powershell
$body = @{
    query = "Compare CNNs and RNNs"
    language = "en"
    top_k = 10  # Retrieve 10 chunks instead of default 5
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host $response.answer
```

---

### Extract Sources
```powershell
$body = @{
    query = "What are transformers?"
    language = "en"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Answer:"
Write-Host $response.answer
Write-Host "`n`nSources:"
foreach ($source in $response.sources) {
    Write-Host "[$($source.index)] $($source.source)"
    Write-Host "   Authors: $($source.authors -join ', ')"
    Write-Host "   Date: $($source.publication_date)"
    Write-Host ""
}
```

---

### RAG Query (Without Agents)

For faster retrieval without multi-agent processing:
```powershell
$body = @{
    query = "neural networks"
    top_k = 5
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/rag/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

foreach ($doc in $response.documents) {
    Write-Host "Source: $($doc.source)"
    Write-Host "Score: $($doc.score)"
    Write-Host "Content: $($doc.content.Substring(0, [Math]::Min(200, $doc.content.Length)))..."
    Write-Host ""
}
```

---

## 🌐 Multilingual Queries

### German
```powershell
$body = @{
    query = "Was ist maschinelles Lernen?"
    language = "de"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host $response.answer
```

### French
```powershell
$body = @{
    query = "Qu'est-ce que l'apprentissage automatique?"
    language = "fr"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host $response.answer
```

### Spanish
```powershell
$body = @{
    query = "¿Qué es el aprendizaje automático?"
    language = "es"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host $response.answer
```

---

## 📊 Checking Status

### Index Statistics
```bash
curl http://localhost:8000/rag/stats
```

**Output**:
```json
{
  "total_documents": 15,
  "total_chunks": 642,
  "sources": ["paper1.pdf", "paper2.pdf", ...],
  "index_size_mb": 12.5
}
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Readiness Check
```bash
curl http://localhost:8000/ready
```

**Output**:
```json
{
  "status": "ok",
  "weaviate_ok": true,
  "ollama_ok": true
}
```

---

## 🔄 Batch Processing

### Ingest Multiple Topics
```powershell
$topics = @("machine learning", "deep learning", "neural networks")

foreach ($topic in $topics) {
    Write-Host "Ingesting: $topic"
    
    $body = @{
        query = $topic
        max_results = 3
    } | ConvertTo-Json
    
    Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
    
    Start-Sleep -Seconds 5  # Rate limiting
}

Write-Host "✅ All topics ingested"
```

### Query Multiple Questions
```powershell
$questions = @(
    "What is machine learning?",
    "What are neural networks?",
    "Explain deep learning"
)

foreach ($question in $questions) {
    Write-Host "`nQuestion: $question"
    
    $body = @{
        query = $question
        language = "en"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
    
    Write-Host "Answer: $($response.answer.Substring(0, [Math]::Min(200, $response.answer.Length)))..."
}
```

---

## 📚 Related Documentation

- **[Python Examples](PYTHON_EXAMPLES.md)** - Integration code
- **[n8n Setup & Workflows](../setup/N8N.md)** - Automation examples
- **[API Reference](../api/ENDPOINTS.md)** - All endpoints

---

**[⬅ Back to Examples](README.md)**