# Installation Guide

## System Requirements

### Minimum
- CPU: 4 cores
- RAM: 16GB
- Disk: 20GB free
- OS: Windows 10/11, macOS, or Linux

### Recommended
- CPU: 8+ cores
- RAM: 32GB
- Disk: 50GB SSD
- GPU: NVIDIA (optional, for faster inference)

## Step-by-Step Installation

### 1. Install Docker Desktop

**Windows**:
1. Download from https://www.docker.com/products/docker-desktop
2. Run installer
3. Enable WSL 2 when prompted
4. Reboot

**macOS**:
```bash
brew install --cask docker
```

**Linux**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 2. Clone Repository
```bash
git clone https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git
cd BIS5151E_Research-Assistant
```

### 3. Configure Environment

#### Application Environment (.env)
```bash
cp .env.example .env
```

Edit `.env`:
```env
# LLM Configuration
LLM_MODEL=qwen2.5:3b
OLLAMA_HOST=http://ollama:11434

# RAG Configuration  
WEAVIATE_URL=http://weaviate:8080
RAG_CHUNK_SIZE=350
RAG_TOP_K=5

# Development
ALLOW_SCHEMA_RESET=true  # Set false in production
```

#### Docker Environment (docker/.env)
```bash
cp docker/.env.example docker/.env
```

Edit `docker/.env`:
```env
# PostgreSQL (REQUIRED)
POSTGRES_PASSWORD=your_secure_password_here

# n8n Encryption (REQUIRED)
# Generate with: openssl rand -hex 32
N8N_ENCRYPTION_KEY=your_32_char_hex_key_here
```

### 4. Start Services

**CPU Mode** (default):
```bash
docker compose -f docker/docker-compose.yml up -d
```

**GPU Mode** (NVIDIA only):
```bash
# First, verify GPU support
./scripts/setup/verify_gpu.sh

# Then start with GPU
docker compose -f docker/docker-compose.yml -f docker/docker-compose.nvidia.yml up -d
```

### 5. Wait for Services to Start

Services take 2-5 minutes to fully initialize:
```bash
# Watch logs
docker compose -f docker/docker-compose.yml logs -f

# Or check health
./scripts/admin/health_check.py
```

### 6. Verify Installation
```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8100/health

# Or run comprehensive test
python scripts/admin/health_check.py
```

## Common Issues

### Issue: Services fail to start
**Solution**:
1. Check Docker has enough resources (Settings → Resources)
2. Verify ports 5432, 5678, 8000, 8080, 8100, 11434 are free
3. Check logs: `docker compose logs <service>`

### Issue: Weaviate unhealthy
**Solution**:
```bash
docker compose restart weaviate
docker compose logs weaviate
```

### Issue: Ollama model not found
**Solution**:
```bash
# Pull model manually
docker compose exec ollama ollama pull qwen2.5:3b
```

See [Troubleshooting Guide](../troubleshooting/README.md) for more issues.

## Next Steps

- [Ingest Sample Data](QUICKSTART.md#ingest-data)
- [Run First Query](QUICKSTART.md#query)
- [Configure n8n Workflows](../n8n/README.md)