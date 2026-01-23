# Setup & Installation Guide

Complete guide for installing and configuring ResearchAssistantGPT.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [GPU Setup (Optional)](#gpu-setup-optional)
7. [Troubleshooting](#troubleshooting)
8. [Next Steps](#next-steps)

---

## System Requirements

### Minimum
- **CPU**: 4 cores
- **RAM**: 16GB
- **Disk**: 20GB free space
- **OS**: Windows 10/11, macOS 11+, or Linux (Ubuntu 20.04+)
- **Docker**: Docker Desktop 4.0+ or Docker Engine 20.10+

### Recommended
- **CPU**: 8+ cores
- **RAM**: 32GB
- **Disk**: 50GB SSD
- **GPU**: NVIDIA GPU with 8GB+ VRAM (optional, for faster inference)

---

## Prerequisites

### 1. Install Docker Desktop

**Windows**:
1. Download from https://www.docker.com/products/docker-desktop
2. Run installer and follow prompts
3. Enable WSL 2 when asked
4. Restart computer

**macOS**:
```bash
brew install --cask docker
```

**Linux (Ubuntu/Debian)**:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
```

### 2. Verify Docker Installation
```bash
docker --version
docker compose version

# Expected output:
# Docker version 24.0.7+
# Docker Compose version v2.23.0+
```

### 3. Configure Docker Resources

**Docker Desktop** (Windows/macOS):
1. Open Docker Desktop
2. Go to Settings → Resources
3. Allocate:
   - **CPUs**: At least 4 (recommend 6-8)
   - **Memory**: At least 16GB (recommend 24GB)
   - **Swap**: 2GB
   - **Disk**: At least 50GB

---

## Installation Steps

### Step 1: Clone Repository
```bash
git clone https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git
cd BIS5151E_Research-Assistant
```

### Step 2: Configure Environment Variables

#### Application Environment (.env)
```bash
cp .env.example .env
```

Edit `.env` with your preferred text editor. **Key settings**:
```env
# LLM Configuration
LLM_MODEL=qwen2.5:3b              # Model to use
OLLAMA_HOST=http://ollama:11434   # Keep as-is for Docker

# RAG Configuration
WEAVIATE_URL=http://weaviate:8080 # Keep as-is for Docker
RAG_CHUNK_SIZE=350                # Document chunk size
RAG_CHUNK_OVERLAP=60              # Overlap between chunks
RAG_TOP_K=5                       # Number of results to retrieve

# Development Settings
ALLOW_SCHEMA_RESET=true           # Set to false in production
LOG_LEVEL=INFO                    # DEBUG for more verbose logging
```

#### Docker Secrets (docker/.env)
```bash
cp docker/.env.example docker/.env
```

Edit `docker/.env`. **These are REQUIRED**:
```env
# PostgreSQL Database Password
# IMPORTANT: Change this to a secure password!
POSTGRES_PASSWORD=your_secure_password_here

# n8n Encryption Key
# IMPORTANT: Generate a secure key!
# Generate with: openssl rand -hex 32
N8N_ENCRYPTION_KEY=your_64_character_hex_key_here
```

**Generate secure n8n key**:
```bash
# Linux/macOS/WSL
openssl rand -hex 32

# Windows PowerShell
-join ((0..31) | ForEach-Object { "{0:X2}" -f (Get-Random -Maximum 256) })
```

### Step 3: Start Services

**CPU Mode** (default):
```bash
docker compose -f docker/docker-compose.yml up -d
```

**GPU Mode** (NVIDIA only - see [GPU Setup](#gpu-setup-optional)):
```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.nvidia.yml up -d
```

### Step 4: Wait for Services to Initialize

Services take **2-5 minutes** to fully start. Monitor progress:
```bash
# Watch logs
docker compose -f docker/docker-compose.yml logs -f

# Check service status
docker compose -f docker/docker-compose.yml ps

# All services should show "Up (healthy)"
```

---

## Configuration

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 8000 | Main REST API |
| CrewAI Service | 8100 | Multi-agent workflow |
| n8n | 5678 | Workflow automation UI |
| Weaviate | 8080 | Vector database |
| Ollama | 11434 | LLM inference |
| PostgreSQL | 5432 | Database (internal) |

### Access Points

- **API Documentation**: http://localhost:8000/docs
- **n8n UI**: http://localhost:5678
- **Weaviate Console**: http://localhost:8080/v1/meta

### Initial n8n Setup

1. Open http://localhost:5678
2. Create admin account (first time only)
3. Configure credentials:
   - API Base URL: `http://api:8000` (internal Docker network)
   - No authentication required (local setup)

---

## Verification

### Automated Health Check
```bash
python scripts/admin/health_check.py
```

Expected output:
```
✅ API Health: OK
✅ API Ready: OK
✅ CrewAI: OK
✅ Weaviate: OK
✅ Ollama: OK
✅ n8n: OK
```

### Manual Verification

**1. API Health**:
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

**2. API Readiness**:
```bash
curl http://localhost:8000/ready
# Expected: {"status":"ok","weaviate_ok":true,"ollama_ok":true}
```

**3. Ollama Models**:
```bash
curl http://localhost:8000/ollama/models
# Should list qwen2.5:3b
```

**4. Weaviate**:
```bash
curl http://localhost:8080/v1/meta
# Should return version info
```

---

## GPU Setup (Optional)

GPU acceleration provides **3-5x faster inference** but is optional.

### NVIDIA GPU Setup

**Prerequisites**:
- NVIDIA GPU with CUDA support
- NVIDIA Driver 525+ installed on host
- NVIDIA Container Toolkit

**Linux Installation**:
```bash
# Run automated setup
sudo ./scripts/setup/install_gpu_support_linux.sh
```

**Windows Installation**:
```powershell
# Run as Administrator
.\scripts\setup\install_gpu_support_windows.ps1
```

**Manual Installation** (Linux):
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

**Start with GPU**:
```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.nvidia.yml up -d
```

**Verify GPU Access**:
```bash
docker compose exec ollama nvidia-smi
# Should show GPU info
```

### AMD GPU Setup

⚠️ **Warning**: AMD GPU support is experimental and limited.

See [GPU Setup Guide](GPU_SETUP.md) for AMD-specific instructions.

---

## Troubleshooting

### Issue: Services Fail to Start

**Symptoms**: Services keep restarting or show "unhealthy"

**Solutions**:
1. Check Docker has enough resources (16GB+ RAM)
2. Verify ports are not in use:
```bash
   # Check if ports are free
   netstat -an | grep -E "8000|8080|5678|11434"
```
3. Check service logs:
```bash
   docker compose logs <service-name>
   # Example: docker compose logs weaviate
```

### Issue: "Cannot Connect to Docker Daemon"

**Solution** (Linux):
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then test
docker ps
```

**Solution** (Windows/macOS):
- Ensure Docker Desktop is running
- Check system tray for Docker icon

### Issue: Ollama Model Not Found

**Symptoms**: `ollama_ok: false` in readiness check

**Solution**:
```bash
# Pull model manually
docker compose exec ollama ollama pull qwen2.5:3b

# Wait for download to complete (~2GB)
# Then verify
curl http://localhost:8000/ollama/models
```

### Issue: Weaviate Unhealthy

**Solution**:
```bash
# Restart Weaviate
docker compose restart weaviate

# Wait 30 seconds, then check
curl http://localhost:8080/v1/.well-known/ready
```

### Issue: Port Already in Use

**Symptom**: `Error: port is already allocated`

**Solution**:
```bash
# Find process using port (example: 8000)
# Linux/macOS
lsof -i :8000

# Windows PowerShell
netstat -ano | findstr :8000

# Kill the process or change port in docker-compose.yml
```

---

## Next Steps

After successful installation:

### 1. Ingest Sample Data

**Option A: ArXiv Papers** (recommended for testing):
```bash
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "max_results": 3}'
```

**Option B: Local Files**:
```bash
# Add PDF/TXT files to data/raw/
# Then ingest
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*"}'
```

### 2. Run Your First Query
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "language": "en"
  }'
```

### 3. Explore the API

- **Interactive Docs**: http://localhost:8000/docs
- **API Reference**: [docs/api/README.md](../api/README.md)

### 4. Set Up n8n Workflows

1. Open http://localhost:5678
2. Import example workflows from `docker/workflows/`
3. Configure workflow credentials

See [Workflow Examples](../examples/workflow_examples.md)

### 5. Development Setup (Optional)

If you want to modify code:
```bash
# Open in VS Code DevContainer
code .
# VS Code will prompt to "Reopen in Container"
```

---

## Additional Resources

- **[API Documentation](../api/README.md)** - Complete API reference
- **[Architecture Guide](../architecture/README.md)** - System design
- **[Troubleshooting Guide](../troubleshooting/README.md)** - Common issues
- **[Usage Examples](../examples/README.md)** - Code examples

---

## Getting Help

- **GitHub Issues**: https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues
- **Course Forum**: [Link to course platform]
- **Team Contact**: [Your team's contact method]

---

**[⬆ Back to Main README](../../README.md)**