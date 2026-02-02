# QuickStart Guide

Get ResearchAssistantGPT running in **5 minutes**.

For detailed installation instructions, see [docs/setup/INSTALLATION.md](docs/setup/INSTALLATION.md).

---

## Prerequisites

Before starting, ensure you have:

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Docker Desktop** | 20.10+ | Latest |
| **RAM** | 16GB | 32GB |
| **Disk Space** | 20GB free | 50GB free SSD |
| **OS** | Windows 10, macOS 10.15, Ubuntu 20.04 | Latest versions |

**Install Docker Desktop**: https://www.docker.com/products/docker-desktop

---

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git
cd BIS5151E_Research-Assistant
```

### 2. Configure Environment

**Application environment** (REQUIRED):
```bash
cp .env.example .env
# Edit .env if you want to change settings
```

**Docker environment** (REQUIRED):
```bash
cp docker/.env.example docker/.env
```

**Edit `docker/.env` and set these required values**:
```env
# REQUIRED: Set a secure PostgreSQL password
POSTGRES_PASSWORD=your_secure_password_here

# REQUIRED: Generate a 32-character hex key for n8n
# Linux/macOS/WSL: openssl rand -hex 32
# Windows PowerShell: -join ((0..31) | ForEach-Object { "{0:X2}" -f (Get-Random -Maximum 256) })
N8N_ENCRYPTION_KEY=your_64_character_hex_key_here
```

**Generate encryption key**:
```bash
# Linux/macOS/WSL
openssl rand -hex 32

# Windows PowerShell
-join ((0..31) | ForEach-Object { "{0:X2}" -f (Get-Random -Maximum 256) })
```

### 3. Start Services
```bash
docker compose -f docker/docker-compose.yml up -d
```

**Expected output**:
```
[+] Running 7/7
 ✔ Network research_net    Created
 ✔ Container postgres      Started
 ✔ Container weaviate      Started
 ✔ Container ollama        Started
 ✔ Container n8n           Started
 ✔ Container api           Started
 ✔ Container crewai        Started
```

### 4. Wait for Services (2-3 minutes)

**Monitor startup**:
```bash
docker compose -f docker/docker-compose.yml logs -f
# Press Ctrl+C when you see "Application startup complete"
```

**Or check health**:
```bash
# Wait until all services show "healthy"
docker compose -f docker/docker-compose.yml ps
```

### 5. Verify Installation
```bash
# API health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# API readiness (checks Weaviate, Ollama)
curl http://localhost:8000/ready
# Expected: {"status":"ok","weaviate_ok":true,"ollama_ok":true}
```

**Or run automated health check**:
```bash
python scripts/admin/health_check.py
```

---

## First Query

### Option 1: Using PowerShell / Command Line

**Step 1a: Ingest sample papers from ArXiv**
```powershell
# PowerShell (Windows)
$body = @{
    query = "transformers attention mechanism"
    max_results = 3
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Ingested: $($response.documents_loaded) documents"
```
```bash
# Linux/macOS (curl)
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query":"transformers attention mechanism","max_results":3}'
```

Wait ~30-60 seconds for response:
```json
{
  "source": "arxiv",
  "documents_loaded": 3,
  "chunks_created": 142,
  "chunks_ingested": 142,
  "success": true
}
```

**Step 1b: Or ingest local documents**

Place PDFs or TXT files in `data/raw/`, then:
```powershell
# PowerShell (Windows)
$body = @{
    pattern = "*"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/local" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Ingested: $($response.documents_loaded) documents"
```
```bash
# Linux/macOS (curl)
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern":"*"}'
```

**Step 2: Query the system**
```powershell
# PowerShell (Windows)
$body = @{
    query = "Explain the transformer attention mechanism"
    language = "en"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "`nAnswer:`n$($response.answer)"
```
```bash
# Linux/macOS (curl)
curl -X POST http://localhost:8000/research/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Explain the transformer attention mechanism","language":"en"}'
```

### Option 2: Using API Docs (Swagger UI)

1. **Open API docs**: http://localhost:8000/docs

2. **Ingest papers**:
   - Click **POST /rag/ingest/arxiv** (or **POST /rag/ingest/local** for local files)
   - Click "Try it out"
   - For ArXiv, enter:
```json
     {
       "query": "machine learning",
       "max_results": 3
     }
```
   - For local files, enter:
```json
     {
       "pattern": "*"
     }
```
   - Click "Execute"
   - Wait for response (30-60 seconds)

3. **Query**:
   - Click **POST /research/query**
   - Click "Try it out"
   - Enter:
```json
     {
       "query": "What is machine learning?",
       "language": "en"
     }
```
   - Click "Execute"

### Option 3: Using Python
```python
import requests
import json

# Ingest papers
response = requests.post(
    "http://localhost:8000/rag/ingest/arxiv",
    json={"query": "neural networks", "max_results": 3}
)
print(f"Ingested: {response.json()['documents_loaded']} papers")

# Query
response = requests.post(
    "http://localhost:8000/research/query",
    json={
        "query": "What are neural networks?",
        "language": "en"
    }
)
result = response.json()
print(f"\nAnswer:\n{result['answer']}")
```

---

## Access Points

Once running, access these services:

| Service | URL | Purpose |
|---------|-----|---------|
| **API Documentation** | http://localhost:8000/docs | Interactive API docs |
| **n8n Workflow UI** | http://localhost:5678 | Workflow automation |
| **Weaviate Console** | http://localhost:8080/v1/meta | Vector database info |

---

## Next Steps

### 1. Set Up n8n Workflows

See **[n8n Setup Guide](docs/setup/N8N.md)** for:
- Creating n8n admin account
- Importing example workflows
- Setting up scheduled research tasks
- Configuring email notifications


### 2. Explore the API

**Available endpoints**:
- `POST /rag/ingest/arxiv` - Fetch papers from ArXiv
- `POST /rag/ingest/local` - Ingest local PDFs
- `POST /research/query` - Complete research workflow (ingest + query)
- `POST /rag/query` - Query only (no ingestion)
- `GET /rag/stats` - View index statistics
- `GET /health` - Health check
- `GET /ready` - Readiness check

Full documentation: **[API Reference](docs/api/ENDPOINTS.md)**

### 3. Ingest Your Own Documents
```bash
# Place PDFs or TXT files in data/raw/
cp your_paper.pdf data/raw/

# Ingest them
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*"}'
```

### 4. Try Multilingual Queries
```powershell
# PowerShell (Windows)

# German
$body = @{
    query = "Was ist maschinelles Lernen?"
    language = "de"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# French
$body = @{
    query = "Qu'est-ce que l'apprentissage automatique?"
    language = "fr"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# Spanish
$body = @{
    query = "¿Qué es el aprendizaje automático?"
    language = "es"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```
```bash
# Linux/macOS (curl)

# German
curl -X POST http://localhost:8000/research/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Was ist maschinelles Lernen?","language":"de"}'

# French
curl -X POST http://localhost:8000/research/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Qu'\''est-ce que l'\''apprentissage automatique?","language":"fr"}'

# Spanish
curl -X POST http://localhost:8000/research/query \
  -H "Content-Type: application/json" \
  -d '{"query":"¿Qué es el aprendizaje automático?","language":"es"}'
```

---

## Stopping Services
```bash
# Stop all services (keeps data)
docker compose -f docker/docker-compose.yml down

# Stop and remove all data (fresh start)
docker compose -f docker/docker-compose.yml down -v
```

---

## Common Issues

### Issue: Port already in use

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**:
```bash
# Find what's using the port
# Linux/macOS:
lsof -i :8000

# Windows:
netstat -ano | findstr :8000

# Kill the process or change the port in docker/.env
```

### Issue: Ollama model not found

**Error**: `Model 'qwen3:1.7b' not found`

**Solution**:
```bash
# Pull the model manually
docker compose exec ollama ollama pull qwen3:1.7b

# Or pull all models
docker compose exec ollama ollama pull qwen3:4b
docker compose exec ollama ollama pull qwen2.5:3b
```

### Issue: Services fail to start

**Solution**:
```bash
# Check Docker has enough resources
# Docker Desktop → Settings → Resources
# Ensure: 4+ CPUs, 8GB+ RAM, 20GB+ disk

# Check logs
docker compose -f docker/docker-compose.yml logs

# Restart services
docker compose -f docker/docker-compose.yml restart
```

### Issue: Ollama Desktop App Blocking Port

**Error**: `Failed to connect to Ollama at localhost:11434`

**Cause**: Ollama desktop application is running and blocking port 11434.

**Solution**:
```bash
# Windows: Right-click Ollama tray icon → Quit
# macOS: Click Ollama menu bar icon → Quit Ollama
# Linux: killall ollama

# Then restart Docker services
docker compose -f docker/docker-compose.yml restart ollama
```

For more troubleshooting, see [docs/setup/TROUBLESHOOTING.md](docs/setup/TROUBLESHOOTING.md).

---

## Getting Help

- **Documentation**: [docs/README.md](docs/README.md)
- **Complete Installation**: [docs/setup/INSTALLATION.md](docs/setup/INSTALLATION.md)
- **API Reference**: [docs/api/ENDPOINTS.md](docs/api/ENDPOINTS.md)
- **Command Reference**: [docs/guides/COMMAND_REFERENCE.md](docs/guides/COMMAND_REFERENCE.md)
- **Troubleshooting**: [docs/setup/TROUBLESHOOTING.md](docs/setup/TROUBLESHOOTING.md)
- **Issues**: [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/discussions)

---

**🎉 You're ready to use ResearchAssistantGPT!**

**[⬅ Back to README](README.md)** | **[➡ Next: Complete Installation Guide](docs/setup/INSTALLATION.md)**