# Docker Configuration Guide

Advanced Docker Compose configuration and troubleshooting.

---

## Overview

ResearchAssistantGPT uses **Docker Compose** to orchestrate multiple services:

| Service | Image | Purpose | Ports |
|---------|-------|---------|-------|
| **postgres** | postgres:15 | n8n database | 5432 |
| **weaviate** | weaviate/weaviate:1.23.0 | Vector database | 8080 |
| **ollama** | ollama/ollama:latest | LLM inference | 11434 |
| **n8n** | n8nio/n8n:latest | Workflow automation | 5678 |
| **api** | (custom build) | FastAPI server | 8000 |
| **crewai** | (custom build) | Agent service | 8001 |

---

## Docker Compose Files

### Main File
```
docker/docker-compose.yml
```
**Default configuration** for CPU-based deployment.

### GPU Support (Coming Soon)
```
docker/docker-compose.nvidia.yml  # NVIDIA GPUs
docker/docker-compose.amd.yml     # AMD GPUs
```

---

## Configuration

### Environment Variables

**File:** `docker/.env`
```bash
# PostgreSQL
POSTGRES_DB=n8n
POSTGRES_USER=n8n
POSTGRES_PASSWORD=your_password

# n8n
N8N_ENCRYPTION_KEY=your_32_char_key
N8N_HOST=localhost
N8N_PORT=5678

# Ports (change if defaults conflict)
API_PORT=8000
WEAVIATE_PORT=8080
OLLAMA_PORT=11434
POSTGRES_PORT=5432

# Ollama
OLLAMA_MODEL=qwen2.5:3b

# Weaviate
WEAVIATE_HOST=weaviate
WEAVIATE_PORT=8080
```

### Port Mapping

**Default ports:**
- `8000` → API
- `5678` → n8n
- `8080` → Weaviate
- `11434` → Ollama
- `5432` → PostgreSQL

**Change ports** if they conflict:
```bash
# Edit docker/.env
API_PORT=9000
N8N_PORT=9678
WEAVIATE_PORT=9080
```

---

## Service Management

### Start Services
```bash
# All services
docker compose -f docker/docker-compose.yml up -d

# Specific service
docker compose up -d api
```

### Stop Services
```bash
# All services
docker compose -f docker/docker-compose.yml down

# Specific service
docker compose stop api
```

### Restart Service
```bash
docker compose restart api
```

### View Logs
```bash
# All services (follow mode)
docker compose logs -f

# Specific service
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api
```

### Check Status
```bash
docker compose ps
```

---

## Volumes & Data Persistence

### Named Volumes
```yaml
volumes:
  postgres_data:      # PostgreSQL data
  weaviate_data:      # Vector embeddings
  ollama_data:        # LLM models
  n8n_data:           # Workflow data
```

### Bind Mounts
```yaml
volumes:
  - ./data:/app/data           # Document storage
  - ./outputs:/app/outputs     # Generated summaries
  - ./configs:/app/configs     # Configuration files
```

### Backup Data
```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U n8n n8n > backup_postgres.sql

# Backup Weaviate
docker compose exec weaviate \
  curl -X POST http://localhost:8080/v1/backups/filesystem
```

### Restore Data
```bash
# Restore PostgreSQL
docker compose exec -T postgres psql -U n8n n8n < backup_postgres.sql

# Restore Weaviate
docker compose exec weaviate \
  curl -X POST http://localhost:8080/v1/backups/filesystem/restore
```

### Reset All Data
```bash
# ⚠️ WARNING: This deletes ALL data
docker compose down -v
```

---

## Networking

### Internal Network

Services communicate via `research_net` network using service names:
```python
# From API container, connect to Weaviate
WEAVIATE_URL = "http://weaviate:8080"  # ✅ Correct

# NOT
WEAVIATE_URL = "http://localhost:8080"  # ❌ Wrong (won't work in containers)
```

### Service Dependencies
```yaml
depends_on:
  weaviate:
    condition: service_healthy
  ollama:
    condition: service_started
```

Ensures services start in correct order.

---

## Resource Limits

### Configure Limits

**Edit `docker-compose.yml`:**
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Monitor Resource Usage
```bash
# Real-time stats
docker stats

# Specific service
docker stats api
```

---

## Building Images

### Build All Images
```bash
docker compose -f docker/docker-compose.yml build
```

### Build Specific Service
```bash
docker compose build api
```

### No-Cache Build
```bash
docker compose build --no-cache api
```

### Multi-Stage Builds

Our Dockerfile uses multi-stage builds:
```dockerfile
FROM python:3.11-slim as base
# Base dependencies

FROM base as api
# API-specific setup

FROM base as crewai
# CrewAI-specific setup
```

---

## Health Checks

### Service Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Check Health Status
```bash
docker compose ps
# Look for "healthy" status
```

---

## Troubleshooting

### Services Won't Start

**Check logs:**
```bash
docker compose logs api
```

**Common causes:**
- Port conflicts
- Missing environment variables
- Insufficient Docker resources

### Port Conflicts

**Find process using port:**
```bash
# Linux/macOS
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

**Solutions:**
1. Kill the conflicting process
2. Change port in `docker/.env`

### Out of Memory

**Symptoms:**
- Services crash randomly
- Docker logs show "Killed"

**Solution:**
1. Increase Docker memory allocation (Settings → Resources)
2. Add resource limits to services
3. Reduce concurrent operations

### Network Issues

**Service can't reach another service:**
```bash
# Test connectivity from inside container
docker compose exec api ping weaviate
docker compose exec api curl http://weaviate:8080/v1/meta
```

**Common fixes:**
- Use service names, not `localhost`
- Verify `research_net` network exists: `docker network ls`
- Restart Docker

### Slow Performance

**Causes:**
- Insufficient RAM
- CPU throttling
- Disk I/O bottleneck

**Solutions:**
1. Allocate more resources to Docker
2. Use SSD for Docker storage
3. Enable [GPU support](GPU.md)

### Permission Errors (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in

# Verify
docker ps
```

---

## Advanced Configuration

### Custom Networks
```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

### Docker Profiles
```bash
# Start with specific profile
docker compose --profile dev up -d
```
```yaml
services:
  devcontainer:
    profiles: ["dev"]
    # Only starts with --profile dev
```

### Override Files

**Create `docker-compose.override.yml`:**
```yaml
services:
  api:
    environment:
      - DEBUG=true
    ports:
      - "8001:8000"  # Different host port
```

Automatically merged with main compose file.

---

## Production Deployment

### Security Checklist

- [ ] Change default passwords
- [ ] Use secrets management
- [ ] Enable HTTPS
- [ ] Restrict network access
- [ ] Regular backups
- [ ] Update images regularly

### Secrets Management
```yaml
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt

services:
  postgres:
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
```

### HTTPS Configuration

**Use reverse proxy (nginx, traefik):**
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
```

---

## Useful Commands
```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# Remove stopped containers
docker compose rm

# Remove unused images
docker image prune

# Remove everything (⚠️ dangerous)
docker system prune -a --volumes

# Export container filesystem
docker export api > api_backup.tar

# Check container resource usage
docker stats --no-stream

# Execute command in running container
docker compose exec api bash
```

---

## Next Steps

- 🚀 [GPU Support](GPU.md) - Enable GPU acceleration
- 💻 [Development Setup](DEVELOPMENT.md) - Dev environment
- 🔧 [Troubleshooting](../troubleshooting/README.md) - Common issues

---

**[⬅ Back to Setup](README.md)** | **[⬆ Back to Main README](../../README.md)**