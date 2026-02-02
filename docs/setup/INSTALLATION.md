# Complete Installation Guide

Comprehensive step-by-step installation instructions for ResearchAssistantGPT.

For a quick 5-minute setup, see [QUICKSTART.md](../../QUICKSTART.md).

---

## Table of Contents

- [System Requirements](#system-requirements)
- [Prerequisites Installation](#prerequisites-installation)
- [Repository Setup](#repository-setup)
- [Environment Configuration](#environment-configuration)
- [Starting Services](#starting-services)
- [Verification](#verification)
- [First Query](#first-query)
- [Post-Installation](#post-installation)
- [Common Startup Issues](#common-startup-issues)
- [Next Steps](#next-steps)

---

## System Requirements

### Minimum Requirements

| Component | Specification |
|-----------|--------------|
| **CPU** | 4 cores (x86_64) |
| **RAM** | 16GB |
| **Disk** | 20GB free space |
| **OS** | Windows 10/11, macOS 10.15+, Ubuntu 20.04+ |
| **Network** | Internet (for Docker images & ArXiv) |

### Recommended Requirements

| Component | Specification |
|-----------|--------------|
| **CPU** | 8+ cores (x86_64) |
| **RAM** | 32GB |
| **Disk** | 50GB SSD |
| **GPU** | NVIDIA GPU with 8GB+ VRAM (optional) |
| **OS** | Windows 11, macOS 13+, Ubuntu 22.04+ |

### Software Prerequisites

| Software | Version | Required |
|----------|---------|----------|
| **Docker Desktop** | 20.10+ | ✅ Required |
| **Docker Compose** | 2.0+ | ✅ Required (included with Docker Desktop) |
| **Git** | 2.30+ | ✅ Required |
| **Python** | 3.11 | ⚠️ Optional (for local development) |
| **VS Code** | Latest | ⚠️ Optional (recommended for development) |

---

## Prerequisites Installation

### 1. Install Docker Desktop

Docker Desktop includes Docker Engine and Docker Compose.

#### Windows

1. Download: https://www.docker.com/products/docker-desktop
2. Run installer: `Docker Desktop Installer.exe`
3. Follow wizard (enable WSL 2 when prompted)
4. Restart computer
5. Verify installation:
```powershell
   docker --version
   docker compose version
```

**Windows-specific notes**:
- Enable Hyper-V and WSL 2 (installer will prompt)
- Allocate resources: Docker Desktop → Settings → Resources
  - CPUs: 4+
  - Memory: 8GB+
  - Disk: 20GB+

#### macOS

**Using Homebrew** (recommended):
```bash
brew install --cask docker
```

**Or download**: https://www.docker.com/products/docker-desktop

1. Open `Docker.dmg`
2. Drag Docker to Applications
3. Open Docker from Applications
4. Grant permissions when prompted
5. Verify:
```bash
   docker --version
   docker compose version
```

**macOS-specific notes**:
- For Apple Silicon (M1/M2): Use "Apple Silicon" version
- Allocate resources: Docker Desktop → Preferences → Resources

#### Linux (Ubuntu/Debian)
```bash
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group (avoid sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

### 2. Install Git

#### Windows
```powershell
# Using winget
winget install Git.Git

# Or download: https://git-scm.com/download/win
```

#### macOS
```bash
# Using Homebrew
brew install git

# Or use Xcode Command Line Tools
xcode-select --install
```

#### Linux
```bash
sudo apt-get install git
```

Verify:
```bash
git --version
```

### 3. Optional: Install VS Code

For development work, VS Code with DevContainer is recommended.
```bash
# Windows (winget)
winget install Microsoft.VisualStudioCode

# macOS (Homebrew)
brew install --cask visual-studio-code

# Linux (snap)
sudo snap install code --classic
```

**Recommended VS Code Extensions**:
- Dev Containers (ms-vscode-remote.remote-containers)
- Python (ms-python.python)
- Docker (ms-azuretools.vscode-docker)

---

## Repository Setup

### 1. Clone Repository
```bash
# Clone from GitHub
git clone https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git

# Navigate to project directory
cd BIS5151E_Research-Assistant
```

### 2. Verify Directory Structure
```bash
# List main directories
ls -la

# Expected output should include:
# .devcontainer/
# configs/
# data/
# docker/
# docs/
# src/
# tests/
# .env.example
# docker-compose.yml (symlink or actual file)
# README.md
```

---

## Environment Configuration

### 1. Application Environment (.env)

**This file is recommended** - defaults might not work for most users.
```bash
# Copy example
cp .env.example .env
```

**Edit `.env` if you want to customize**:
```bash
nano .env  # or use any text editor
```

**Key settings** (defaults shown):
```env
# LLM Configuration
LLM_MODEL=qwen3:1.7b
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048
OLLAMA_HOST=http://ollama:11434
OLLAMA_TIMEOUT=300

# RAG Configuration
WEAVIATE_URL=http://weaviate:8080
RAG_CHUNK_SIZE=350
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=5
RAG_ALPHA=0.5

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Guardrails
GUARDRAILS_CITATION_REQUIRED=true
GUARDRAILS_STRICT_MODE=false

# Evaluation
EVAL_ENABLE_TRULENS=true
EVAL_ENABLE_PERFORMANCE=true

# Development
ALLOW_SCHEMA_RESET=true
LOG_LEVEL=INFO
```

### 2. Docker Environment (docker/.env)

**This file is REQUIRED** - you must set passwords and keys.
```bash
# Copy example
cp docker/.env.example docker/.env
```

**Edit `docker/.env`**:
```bash
nano docker/.env  # or use any text editor
```

**REQUIRED settings**:
```env
# =============================================================================
# REQUIRED: PostgreSQL Password
# =============================================================================
# Used by: PostgreSQL, n8n
# IMPORTANT: Change this to a strong password!
POSTGRES_PASSWORD=your_secure_password_here

# =============================================================================
# REQUIRED: n8n Encryption Key
# =============================================================================
# Used by: n8n (to encrypt credentials)
# IMPORTANT: Must be 32 characters (64 hex digits)
# Generate with:
#   Linux/macOS: openssl rand -hex 32
#   Windows: -join ((0..31) | ForEach-Object { "{0:X2}" -f (Get-Random -Maximum 256) })
N8N_ENCRYPTION_KEY=your_64_character_hex_key_here
```

**Generate secure values**:

**n8n Encryption Key**:
```bash
# Linux / macOS / WSL
openssl rand -hex 32

# Windows PowerShell
-join ((0..31) | ForEach-Object { "{0:X2}" -f (Get-Random -Maximum 256) })

# Example output (use this format):
# 8a7d9b3c4e1f2a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b
```

**Optional settings** (defaults shown):
```env
# PostgreSQL
POSTGRES_DB=research_assistant
POSTGRES_USER=research_assistant

# Service Ports (change if defaults conflict)
API_PORT=8000
CREWAI_PORT=8100
N8N_PORT=5678
WEAVIATE_PORT=8080
OLLAMA_PORT=11434
POSTGRES_PORT=5432

# Ollama Model (change if you prefer different model)
OLLAMA_MODEL=qwen3:1.7b

# n8n Configuration
N8N_HOST=localhost
WEBHOOK_URL=http://localhost:5678/
```

---

## Starting Services

### 1. Start Docker Compose (CPU Mode)
```bash
# Start all services in detached mode
docker compose -f docker/docker-compose.yml up -d
```

**Expected output**:
```
[+] Running 7/7
 ✔ Network research_net           Created
 ✔ Volume "postgres_data"         Created
 ✔ Volume "weaviate_data"         Created
 ✔ Volume "ollama_data"           Created
 ✔ Volume "n8n_data"              Created
 ✔ Container postgres             Started
 ✔ Container weaviate             Started
 ✔ Container ollama               Started
 ✔ Container ollama-init          Started
 ✔ Container n8n                  Started
 ✔ Container api                  Started
 ✔ Container crewai               Started
```

### 2. Monitor Startup (Optional)

Services take **2-3 minutes** to fully initialize.

**Watch logs**:
```bash
docker compose -f docker/docker-compose.yml logs -f

# Press Ctrl+C to exit (services keep running)
```

**Check status**:
```bash
docker compose -f docker/docker-compose.yml ps
```

**Expected output** (when ready):
```
NAME        IMAGE                       STATUS
api         research-assistant-api      Up (healthy)
crewai      research-assistant-crewai   Up (healthy)
n8n         n8nio/n8n:latest            Up (healthy)
ollama      ollama/ollama:latest        Up (healthy)
postgres    postgres:15                 Up (healthy)
weaviate    weaviate/weaviate:latest    Up (healthy)
```

### 3. GPU Mode (Optional)

See [GPU.md](GPU.md) for GPU setup with NVIDIA or AMD GPUs.

**Quick start with NVIDIA GPU**:
```bash
# Install NVIDIA Container Toolkit first (see GPU.md)
docker compose -f docker/docker-compose.yml -f docker/docker-compose.nvidia.yml up -d
```

---

## Verification

### Automated Health Check
```bash
# Run health check script
python scripts/admin/health_check.py
```

**Expected output**:
```
🏥 ResearchAssistantGPT Health Check
=====================================

✅ API Service (http://localhost:8000)
   Status: healthy
   Response time: 23ms

✅ CrewAI Service (http://localhost:8100)
   Status: healthy

✅ Weaviate (http://localhost:8080)
   Status: ready
   Version: 1.23.0
   Objects: 0

✅ Ollama (http://localhost:11434)
   Status: running
   Models: qwen3:1.7b

✅ n8n (http://localhost:5678)
   Status: ready

=====================================
All services healthy! ✅
```

### Manual Verification

If the script doesn't work, verify manually:

**1. API Health**:
```bash
curl http://localhost:8000/health

# Expected: {"status":"healthy"}
```

**2. API Readiness** (checks dependencies):
```bash
curl http://localhost:8000/ready

# Expected: {"status":"ok","weaviate_ok":true,"ollama_ok":true}
```

**3. Weaviate**:
```bash
curl http://localhost:8080/v1/meta

# Expected: JSON with version info
```

**4. Ollama**:
```bash
curl http://localhost:11434/api/tags

# Expected: {"models":[{"name":"qwen3:1.7b",...}]}
```

**5. n8n**:
```bash
curl http://localhost:5678/healthz

# Expected: {"status":"ok"}
```

**6. CrewAI**:
```bash
curl http://localhost:8100/health

# Expected: {"status":"healthy"}
```

---

## First Query

### Step 1: Ingest Sample Data

You can ingest data from **ArXiv** (automatic download) or **local files** (PDFs/TXT in `data/raw/`).

#### Option A: Ingest from ArXiv
```powershell
# PowerShell (Windows)
$body = @{
    query = "transformer attention mechanism"
    max_results = 3
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Success: Ingested $($response.documents_loaded) papers"
Write-Host "Chunks created: $($response.chunks_created)"
```
```bash
# Linux/macOS (curl)
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query":"transformer attention mechanism","max_results":3}'
```

**This will**:
1. Search ArXiv for 3 papers on "transformer attention mechanism"
2. Download PDFs (~5-10MB)
3. Extract text from PDFs
4. Chunk into 350-character segments
5. Generate embeddings
6. Store in Weaviate

**Wait ~30-60 seconds** for response:
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

#### Option B: Ingest Local Files

First, place your PDFs or TXT files in `data/raw/`:
```bash
cp /path/to/your/paper.pdf data/raw/
```

Then ingest:
```powershell
# PowerShell (Windows)
$body = @{
    pattern = "*"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/local" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Success: Ingested $($response.documents_loaded) documents"
```
```bash
# Linux/macOS (curl)
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern":"*"}'
```

### Step 2: Query the System
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

Write-Host "`nQuery: $($response.query)"
Write-Host "`nAnswer:`n$($response.answer)"
Write-Host "`nProcessing time: $($response.processing_time) seconds"
```
```bash
# Linux/macOS (curl)
curl -X POST http://localhost:8000/research/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Explain the transformer attention mechanism","language":"en"}'
```

**This will**:
1. Validate query with Guardrails
2. Retrieve top-5 relevant chunks from Weaviate
3. Run multi-agent workflow (Writer → Reviewer → FactChecker)
4. Return fact-checked summary with citations

**Wait ~25-30 seconds** for response:
```json
{
  "query": "Explain the transformer attention mechanism",
  "answer": "The transformer attention mechanism enables models to weigh the importance of different words in a sequence when processing input [1]. It uses query, key, and value matrices to compute attention scores that determine which parts of the input to focus on [2]. This self-attention mechanism allows the model to capture long-range dependencies more effectively than recurrent architectures [3]. The multi-head attention variant applies this process multiple times in parallel, learning different representation subspaces [1][2]...",
  "sources": [...],
  "language": "en",
  "processing_time": 28.4
}
```

---

## Post-Installation

### 1. Set Up n8n

See [N8N.md](N8N.md) for detailed setup.

**Quick steps**:

1. Open http://localhost:5678
2. Create admin account (first-time only)
3. Import example workflow:
   - Settings → Import from File
   - Select `docker/workflows/research_assistant.json`
4. Configure credentials:
   - API URL: `http://api:8000` (use Docker internal network)
   - No authentication needed for local setup

### 2. Ingest Your Own Documents
```bash
# Place PDFs or TXT files in data/raw/
cp /path/to/your/paper.pdf data/raw/
```
```powershell
# PowerShell (Windows)
$body = @{
    pattern = "*"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/local" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Ingested: $($response.documents_loaded) documents from data/raw/"
```
```bash
# Linux/macOS (curl)
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern":"*"}'
```

**Ingest specific files only**:
```powershell
# PowerShell - Ingest only PDF files
$body = @{
    pattern = "*.pdf"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/local" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```
```bash
# Linux/macOS - Ingest only PDF files
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern":"*.pdf"}'
```

### 3. Explore API Documentation

Open http://localhost:8000/docs for interactive API documentation (Swagger UI).

### 4. Development Setup (Optional)

For code development, see [CONTRIBUTING.md](../../CONTRIBUTING.md).

**Quick DevContainer setup**:
```bash
# Open in VS Code
code .

# When prompted: "Reopen in Container" → Click it
# Wait for container to build (2-3 minutes first time)
```

---

## Common Startup Issues

### Issue 1: Ollama Desktop App Blocking Port 11434

**Symptoms**:
- API returns: `Failed to connect to Ollama`
- Ollama container shows port conflict

**Cause**: Ollama desktop application is running and using port 11434.

**Solution**:
```bash
# Windows
# Right-click Ollama icon in system tray → Quit

# macOS
# Click Ollama icon in menu bar → Quit Ollama

# Linux
killall ollama

# Then restart Docker services
docker compose -f docker/docker-compose.yml restart ollama api crewai
```

**Prevent in future**:
```bash
# Disable Ollama autostart
# Windows: Task Manager → Startup → Disable Ollama
# macOS: System Preferences → Users & Groups → Login Items → Remove Ollama
# Linux: Remove from autostart applications
```

### Issue 2: Port Already in Use

**Symptoms**:
- Error: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**:

**Find what's using the port**:
```bash
# Linux/macOS
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

**Option A: Kill the process**:
```bash
# Linux/macOS
kill -9 <PID>

# Windows
taskkill /PID <PID> /F
```

**Option B: Change the port**:
```bash
# Edit docker/.env
API_PORT=9000  # Change 8000 to 9000

# Restart services
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up -d
```

### Issue 3: Weaviate Connection Refused

**Symptoms**:
- API logs show: `ConnectionError: Failed to connect to Weaviate`
- `/ready` endpoint returns `weaviate_ok: false`

**Solution**:
```bash
# Check Weaviate status
docker compose logs weaviate

# Restart Weaviate
docker compose restart weaviate

# Wait 30 seconds, then check
curl http://localhost:8080/v1/meta
```

**If still fails**:
```bash
# Remove Weaviate volume and restart
docker compose down
docker volume rm research-assistant_weaviate_data
docker compose up -d
```

### Issue 4: Ollama Model Not Found

**Symptoms**:
- Error: `Model 'qwen3:1.7b' not found`
- CrewAI logs show model errors

**Solution**:
```bash
# Pull model manually
docker compose exec ollama ollama pull qwen3:1.7b

# Verify
docker compose exec ollama ollama list

# Should show: qwen3:1.7b
```

**Pull all configured models**:
```bash
docker compose exec ollama ollama pull qwen3:1.7b
docker compose exec ollama ollama pull qwen3:4b
docker compose exec ollama ollama pull qwen2.5:3b
```

### Issue 5: Docker Out of Memory

**Symptoms**:
- Services crash randomly
- Docker Desktop shows high memory usage

**Solution**:
```bash
# Increase Docker memory allocation
# Docker Desktop → Settings → Resources
# Set Memory to: 8GB minimum, 16GB recommended

# Restart Docker Desktop
```

### Issue 6: n8n Database Connection Error

**Symptoms**:
- n8n fails to start
- Logs show: `Connection to database failed`

**Solution**:
```bash
# Check postgres is running
docker compose ps postgres

# Check postgres logs
docker compose logs postgres

# Verify password is set in docker/.env
# POSTGRES_PASSWORD must match in .env file

# Restart n8n
docker compose restart postgres n8n
```

For more issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## Next Steps

### 1. Learn the API

- **Interactive Docs**: http://localhost:8000/docs
- **API Reference**: [docs/api/README.md](../api/README.md)

### 2. Set Up Workflows

- **n8n Setup**: [N8N.md](N8N.md)
- **Workflow Examples**: [docs/examples/workflow_examples.md](../examples/workflow_examples.md)

### 3. Enable GPU (Optional)

- **GPU Setup**: [GPU.md](GPU.md)

### 4. Explore Evaluation

- **Evaluation Overview**: [docs/evaluation/README.md](../evaluation/README.md)
- **TruLens Setup**: [docs/evaluation/TRULENS.md](../evaluation/TRULENS.md)

### 5. Start Developing

- **Contributing Guide**: [CONTRIBUTING.md](../../CONTRIBUTING.md)
- **Testing Guide**: [tests/TESTING.md](../../tests/TESTING.md)

---

## Getting Help

- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **GitHub Issues**: https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues
- **GitHub Discussions**: https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/discussions
- **Documentation Hub**: [docs/](../)

---

**[⬅ Back to Quickstart](../../QUICKSTART.md)** | **[⬆ Back to Setup Hub](README.md)** | **[➡ Next: n8n Setup](N8N.md)**