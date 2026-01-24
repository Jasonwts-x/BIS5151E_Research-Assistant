# Installation Guide

Complete step-by-step installation instructions for ResearchAssistantGPT.

---

## Prerequisites

### Required Software

| Software | Minimum Version | Download |
|----------|----------------|----------|
| **Docker Desktop** | 24.0+ | https://www.docker.com/products/docker-desktop |
| **Git** | 2.0+ | https://git-scm.com/downloads |

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 8GB | 16GB+ |
| **Disk Space** | 10GB | 20GB+ |
| **CPU** | 4 cores | 8+ cores |
| **OS** | Windows 10/11, macOS 12+, Ubuntu 20.04+ | Any |

### Docker Configuration

**Allocate sufficient resources to Docker:**

1. Open Docker Desktop
2. Go to Settings → Resources
3. Set:
   - **CPUs**: 4+ cores
   - **Memory**: 8GB minimum (16GB recommended)
   - **Disk**: 20GB+

---

## Installation Steps

### Step 1: Clone Repository
```bash
# Clone the repository
git clone https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git

# Navigate to project directory
cd BIS5151E_Research-Assistant

# Verify you're in the right directory
ls -la  # Should see docker/, src/, tests/, etc.
```

---

### Step 2: Configure Environment

#### 2.1 Create Environment Files
```bash
# Copy example environment files
cp .env.example .env
cp docker/.env.example docker/.env
```

#### 2.2 Edit docker/.env

**Open `docker/.env` in a text editor** and configure:
```bash
# ============================================
# REQUIRED: Set these before starting services
# ============================================

# PostgreSQL (for n8n)
POSTGRES_DB=n8n
POSTGRES_USER=n8n
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD_HERE  # ⚠️ CHANGE THIS

# n8n Configuration
N8N_ENCRYPTION_KEY=YOUR_32_CHAR_KEY_HERE     # ⚠️ CHANGE THIS

# ============================================
# OPTIONAL: Change if defaults conflict
# ============================================

# Service Ports (only change if ports are in use)
# API_PORT=8000
# N8N_PORT=5678
# WEAVIATE_PORT=8080
# OLLAMA_PORT=11434
# POSTGRES_PORT=5432

# Ollama Configuration
# OLLAMA_MODEL=qwen2.5:3b
```

**Generate encryption key:**
```bash
# Linux/macOS:
openssl rand -hex 32

# Windows PowerShell:
-join ((48..57) + (65..70) | Get-Random -Count 32 | % {[char]$_})

# Or use any 32-character alphanumeric string
```

#### 2.3 Edit .env (Optional)

The `.env` file in the root directory is for application-level configuration. Defaults are fine for most users.

---

### Step 3: Start Services

#### 3.1 Start Docker Compose
```bash
# Start all services in detached mode
docker compose -f docker/docker-compose.yml up -d

# Expected output:
# [+] Running 7/7
#  ✔ Network research_net           Created
#  ✔ Container postgres             Started
#  ✔ Container weaviate             Started
#  ✔ Container ollama               Started
#  ✔ Container n8n                  Started
#  ✔ Container api                  Started
#  ✔ Container crewai               Started
```

#### 3.2 Monitor Startup (Optional)
```bash
# Watch logs as services start
docker compose -f docker/docker-compose.yml logs -f

# Press Ctrl+C to exit logs (services keep running)
```

**Services take 2-3 minutes to fully start.**

---

### Step 4: Verify Installation

#### 4.1 Run Health Check
```bash
# Run the health check script
python scripts/admin/health_check.py
```

**Expected output:**
```
🏥 Health Check Results
========================

✅ API Service
   URL: http://localhost:8000
   Status: healthy
   Response time: 45ms

✅ Weaviate
   URL: http://localhost:8080
   Status: ready
   Version: 1.23.0

✅ Ollama
   URL: http://localhost:11434
   Status: running
   Model: qwen2.5:3b

✅ n8n
   URL: http://localhost:5678
   Status: ready

========================
All services healthy! ✅
```

#### 4.2 Manual Verification

If the script doesn't work, check manually:
```bash
# API
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# Weaviate
curl http://localhost:8080/v1/meta
# Should return JSON with version info

# Ollama
curl http://localhost:11434/api/tags
# Should list available models

# n8n
curl http://localhost:5678/healthz
# Should return: {"status":"ok"}
```

---

### Step 5: First Query

#### 5.1 Ingest Sample Data
```bash
# Ingest 3 papers from ArXiv (takes ~30-60 seconds)
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "max_results": 3
  }'
```

**Expected response:**
```json
{
  "source": "arxiv",
  "documents_loaded": 3,
  "chunks_created": 142,
  "chunks_ingested": 142,
  "chunks_skipped": 0,
  "errors": [],
  "success": true
}
```

#### 5.2 Query the System
```bash
# Ask a question
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "language": "en"
  }'
```

**Expected response:**
```json
{
  "query": "What is machine learning?",
  "answer": "Machine learning is a subset of artificial intelligence that enables systems to learn from data... [1][2]",
  "source_documents": [...],
  "language": "en"
}
```

---

## Post-Installation Steps

### 1. Set Up n8n (Optional)

1. **Open n8n**: http://localhost:5678
2. **Create admin account** (first-time only)
3. **Import workflows** from `docker/workflows/`
4. **Configure credentials**:
   - API URL: `http://api:8000` (Docker internal network)

### 2. Explore API Documentation

Open interactive API docs: http://localhost:8000/docs

Try different endpoints:
- `POST /rag/ingest/local` - Ingest local files
- `GET /rag/stats` - View index statistics
- `POST /rag/query` - Query with agents

### 3. Add Your Own Documents
```bash
# Place PDFs in data/raw/
cp ~/Downloads/my-paper.pdf data/raw/

# Ingest them
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*"}'
```

---

## Stopping Services

### Temporary Stop (Preserves Data)
```bash
docker compose -f docker/docker-compose.yml down
```

### Full Reset (Deletes All Data)
```bash
docker compose -f docker/docker-compose.yml down -v
```

---

## Updating the System
```bash
# Pull latest changes
git pull origin main

# Rebuild containers (if Dockerfile changed)
docker compose -f docker/docker-compose.yml build

# Restart services
docker compose -f docker/docker-compose.yml up -d
```

---

## Troubleshooting

### Issue: Port Already in Use
```bash
# Find what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Option 1: Kill the process
# Option 2: Change port in docker/.env
```

### Issue: Services Won't Start
```bash
# Check logs
docker compose -f docker/docker-compose.yml logs

# Check specific service
docker compose logs api
docker compose logs weaviate
```

### Issue: Ollama Model Not Found
```bash
# Manually pull the model
docker compose exec ollama ollama pull qwen2.5:3b

# Verify it's available
docker compose exec ollama ollama list
```

### Issue: Permission Denied (Linux)
```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then try again
```

**More issues?** See [Troubleshooting Guide](../troubleshooting/README.md)

---

## Next Steps

- 📖 [Docker Configuration](DOCKER.md) - Advanced container setup
- 💻 [Development Setup](DEVELOPMENT.md) - Set up dev environment
- 📊 [API Documentation](../api/README.md) - Learn the API
- 🔧 [Examples](../examples/README.md) - Usage examples

---

**[⬅ Back to Setup](README.md)** | **[⬆ Back to Main README](../../README.md)**