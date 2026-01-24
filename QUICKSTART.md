# Quick Start Guide

Get ResearchAssistantGPT running in **10 minutes**.

---

## Prerequisites

Before you begin, ensure you have:

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| **Docker Desktop** | Latest | `docker --version` |
| **Docker Compose** | v2.0+ | `docker compose version` |
| **Git** | Any | `git --version` |
| **Free Disk Space** | 20GB+ | `df -h` |
| **RAM** | 16GB+ | System settings |

**Optional:**
- **VS Code** (for development)
- **Python 3.11** (for local testing)

---

## Installation Steps

### Step 1: Clone Repository
```bash
git clone https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git
cd BIS5151E_Research-Assistant
```

### Step 2: Configure Environment
```bash
# Copy example environment files
cp .env.example .env
cp docker/.env.example docker/.env
```

**Edit `docker/.env`** and set:
```bash
# Required: Set strong passwords
POSTGRES_PASSWORD=your_secure_password_here
N8N_ENCRYPTION_KEY=your_32_char_encryption_key_here

# Optional: Customize ports (if defaults conflict)
# API_PORT=8000
# N8N_PORT=5678
# WEAVIATE_PORT=8080
```

**Generate encryption key:**
```bash
# On Linux/Mac:
openssl rand -hex 32

# On Windows (PowerShell):
-join ((48..57) + (65..70) | Get-Random -Count 32 | % {[char]$_})
```

### Step 3: Start Services
```bash
# Start all services
docker compose -f docker/docker-compose.yml up -d

# View logs (optional)
docker compose -f docker/docker-compose.yml logs -f
```

**Services starting:**
- Postgres (n8n database)
- Weaviate (vector store)
- Ollama (LLM)
- n8n (workflow automation)
- API (FastAPI server)
- CrewAI (agent service)

**Wait 2-3 minutes** for all services to be healthy.

### Step 4: Verify Installation
```bash
# Run health check
python scripts/admin/health_check.py
```

**Expected output:**
```
✅ API: http://localhost:8000 - OK
✅ Weaviate: http://localhost:8080 - OK
✅ Ollama: http://localhost:11434 - OK
✅ n8n: http://localhost:5678 - OK
```

**Troubleshooting:** If any service fails, see [Troubleshooting Guide](docs/troubleshooting/README.md#service-startup-issues).

---

## First Query

### Option 1: Using cURL (Recommended)
```bash
# 1. Ingest sample papers from ArXiv
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "max_results": 3
  }'

# Wait 30-60 seconds for ingestion to complete

# 2. Query the system
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "language": "en"
  }'
```

### Option 2: Using Swagger UI

1. Open http://localhost:8000/docs
2. Click **POST /rag/ingest/arxiv**
3. Click "Try it out"
4. Enter:
```json
   {
     "query": "transformers",
     "max_results": 3
   }
```
5. Click "Execute"
6. Wait for response (30-60 seconds)
7. Click **POST /rag/query**
8. Enter:
```json
   {
     "query": "Explain transformers architecture",
     "language": "en"
   }
```
9. Click "Execute"

### Option 3: Using Python
```python
import requests

# Ingest papers
response = requests.post(
    "http://localhost:8000/rag/ingest/arxiv",
    json={"query": "neural networks", "max_results": 3}
)
print(response.json())

# Query
response = requests.post(
    "http://localhost:8000/rag/query",
    json={
        "query": "What are neural networks?",
        "language": "en"
    }
)
print(response.json()["answer"])
```

---

## Explore the System

### 1. API Documentation
**URL:** http://localhost:8000/docs

**Available Endpoints:**
- `POST /rag/ingest/arxiv` - Fetch papers from ArXiv
- `POST /rag/ingest/local` - Ingest local documents
- `POST /rag/query` - Query with multi-agent processing
- `GET /rag/stats` - View index statistics
- `GET /health` - Health check
- `GET /ready` - Readiness check

### 2. n8n Workflow Automation
**URL:** http://localhost:5678

**First-time setup:**
1. Open http://localhost:5678
2. Create admin account
3. Import example workflows from `docker/workflows/`
4. Configure credentials (API URL: `http://api:8000`)

**Example workflows:**
- Daily ArXiv digest
- Scheduled research summaries
- Email notifications

See [Workflow Examples](docs/examples/workflow_examples.md) for detailed guides.

### 3. Weaviate Console
**URL:** http://localhost:8080/v1/meta

**Check index status:**
```bash
curl http://localhost:8080/v1/objects | jq '.objects | length'
```

---

## Next Steps

Now that your system is running:

1. **📖 Read the Documentation**
   - [API Reference](docs/api/README.md) - Complete endpoint documentation
   - [Architecture Guide](docs/architecture/README.md) - System design
   - [Examples](docs/examples/README.md) - Code examples

2. **🧪 Experiment**
   - Try different queries
   - Ingest your own PDFs (place in `data/raw/`)
   - Create n8n workflows
   - Test multilingual support (DE, FR, ES)

3. **🛠️ Development**
   - [Contributing Guide](CONTRIBUTING.md) - Set up dev environment
   - [Testing Guide](tests/TESTING.md) - Run tests

4. **📊 Monitor**
   - Check logs: `docker compose logs -f`
   - View metrics: http://localhost:8000/metrics (coming soon)

---

## Stopping Services
```bash
# Stop all services
docker compose -f docker/docker-compose.yml down

# Stop and remove volumes (deletes all data)
docker compose -f docker/docker-compose.yml down -v
```

---

## Common Issues

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Either kill the process or change the port in docker/.env
```

### Ollama Model Not Found
```bash
# Pull the model manually
docker compose exec ollama ollama pull qwen2.5:3b
```

### Weaviate Connection Refused
```bash
# Check if Weaviate is running
curl http://localhost:8080/v1/meta

# If not, check logs
docker compose logs weaviate
```

For more issues, see [Troubleshooting Guide](docs/troubleshooting/README.md).

---

## Getting Help

- **Documentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/discussions)

---

**🎉 Congratulations!** You're ready to use ResearchAssistantGPT.

**[⬅ Back to README](README.md)** | **[➡ Next: API Documentation](docs/api/README.md)**