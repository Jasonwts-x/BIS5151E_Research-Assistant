# Troubleshooting Guide

Common issues and solutions for ResearchAssistantGPT.

---

## 🚨 Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| Services won't start | `docker compose down -v && docker compose up -d` |
| Port already in use | Change port in `docker/.env` |
| Slow queries | Restart Ollama: `docker compose restart ollama` |
| Out of memory | Increase Docker RAM allocation |
| Can't connect to Weaviate | Check logs: `docker compose logs weaviate` |

---

## 📋 Table of Contents

- [Installation Issues](#installation-issues)
- [Service Startup Problems](#service-startup-problems)
- [Performance Issues](#performance-issues)
- [Query Errors](#query-errors)
- [Ingestion Problems](#ingestion-problems)
- [Docker Issues](#docker-issues)
- [Network Problems](#network-problems)
- [Data Issues](#data-issues)

---

## Installation Issues

### Issue: Docker Desktop Not Starting

**Symptoms:**
```
Docker Desktop failed to start
Error: Hypervisor not enabled
```

**Solutions:**

**Windows:**
1. Enable Hyper-V in Windows Features
2. Enable virtualization in BIOS
3. Run as Administrator

**macOS:**
1. Check System Preferences → Security
2. Allow Docker in Privacy settings
3. Reinstall Docker Desktop

**Linux:**
1. Check Docker service: `sudo systemctl status docker`
2. Start Docker: `sudo systemctl start docker`
3. Add user to docker group: `sudo usermod -aG docker $USER`

---

### Issue: Git Clone Fails

**Symptoms:**
```
fatal: unable to access 'https://github.com/...': Failed to connect
```

**Solutions:**
```bash
# Check internet connection
ping github.com

# Try SSH instead of HTTPS
git clone git@github.com:Jasonwts-x/BIS5151E_Research-Assistant.git

# Check firewall/proxy settings
git config --global http.proxy http://proxy.example.com:8080
```

---

## Service Startup Problems

### Issue: Services Won't Start

**Symptoms:**
```
ERROR: for weaviate  Container "abc123" is unhealthy
```

**Diagnosis:**
```bash
# Check service status
docker compose ps

# Check logs
docker compose logs weaviate
docker compose logs api
```

**Solutions:**

**1. Restart services:**
```bash
docker compose down
docker compose up -d
```

**2. Full reset:**
```bash
# ⚠️ Deletes all data
docker compose down -v
docker compose up -d
```

**3. Check resources:**
```bash
# View resource usage
docker stats

# Increase Docker memory:
# Docker Desktop → Settings → Resources → Memory → 8GB+
```

---

### Issue: Port Already in Use

**Symptoms:**
```
Error: bind: address already in use 0.0.0.0:8000
```

**Diagnosis:**
```bash
# Find what's using the port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

**Solutions:**

**Option 1: Kill the process**
```bash
# macOS/Linux
kill $(lsof -t -i:8000)

# Windows (find PID first, then)
taskkill /PID <PID> /F
```

**Option 2: Change the port**
```bash
# Edit docker/.env
API_PORT=9000
N8N_PORT=9678
WEAVIATE_PORT=9080

# Restart
docker compose down
docker compose up -d
```

---

### Issue: Ollama Model Not Found

**Symptoms:**
```
Error: model 'qwen2.5:3b' not found
```

**Solution:**
```bash
# Pull the model manually
docker compose exec ollama ollama pull qwen2.5:3b

# Verify
docker compose exec ollama ollama list

# Should show:
# NAME                ID              SIZE
# qwen2.5:3b          abc123def456    2.0 GB
```

---

### Issue: Weaviate Won't Start

**Symptoms:**
```
weaviate  | panic: runtime error: invalid memory address
```

**Solutions:**

**1. Check disk space:**
```bash
df -h  # Need at least 5GB free
```

**2. Reset Weaviate data:**
```bash
docker compose down
docker volume rm research-assistant_weaviate_data
docker compose up -d weaviate
```

**3. Check Weaviate logs:**
```bash
docker compose logs weaviate --tail=50
```

---

## Performance Issues

### Issue: Queries Are Slow (>60 seconds)

**Symptoms:**
```
Query takes 90+ seconds
```

**Diagnosis:**
```bash
# Check Ollama performance
docker stats ollama

# Check if CPU is maxed out
```

**Solutions:**

**1. Reduce context:**
```bash
# Query with fewer documents
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "...",
    "top_k": 3
  }'
```

**2. Restart Ollama:**
```bash
docker compose restart ollama
```

**3. Use smaller model (future):**
```bash
# Edit docker/.env
OLLAMA_MODEL=qwen2.5:1.5b  # Smaller, faster
```

**4. Enable GPU (if available):**
See [GPU Setup Guide](../setup/GPU.md)

---

### Issue: Ingestion Takes Forever

**Symptoms:**
```
Ingesting 5 papers takes 10+ minutes
```

**Diagnosis:**
```bash
# Check network speed
curl -o /dev/null http://arxiv.org/pdf/2301.12345
```

**Solutions:**

**1. Reduce batch size:**
```bash
# Ingest fewer papers at once
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -d '{"query": "...", "max_results": 3}'
```

**2. Check ArXiv availability:**
```bash
# ArXiv may be slow or rate-limiting
# Try again later
```

---

### Issue: High Memory Usage

**Symptoms:**
```
Docker using 12GB+ RAM
Services crashing with OOM errors
```

**Solutions:**

**1. Increase Docker memory:**
```
Docker Desktop → Settings → Resources
Memory: 16GB (recommended)
```

**2. Restart specific service:**
```bash
docker compose restart api
docker compose restart ollama
```

**3. Clear unused data:**
```bash
# Clean Docker system
docker system prune -a

# Remove old logs
docker compose logs --tail=0
```

---

## Query Errors

### Issue: "No context available"

**Symptoms:**
```json
{
  "answer": "No context available for this query."
}
```

**Cause:** No documents in index

**Solution:**
```bash
# Check if index is empty
curl http://localhost:8000/rag/stats

# Ingest documents
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -d '{"query": "machine learning", "max_results": 5}'
```

---

### Issue: Poor Quality Answers

**Symptoms:**
- Answers are generic or off-topic
- No citations
- Hallucinations

**Solutions:**

**1. Improve query specificity:**
```bash
# Bad query
{"query": "AI"}

# Good query
{"query": "How does the transformer attention mechanism work?"}
```

**2. Ingest more relevant papers:**
```bash
# Ingest papers on specific topic
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -d '{"query": "transformer attention mechanism", "max_results": 10}'
```

**3. Increase context (top_k):**
```bash
curl -X POST http://localhost:8000/rag/query \
  -d '{"query": "...", "top_k": 10}'
```

---

### Issue: 500 Internal Server Error

**Symptoms:**
```json
{
  "detail": "Internal Server Error"
}
```

**Diagnosis:**
```bash
# Check API logs
docker compose logs api --tail=50

# Check CrewAI logs
docker compose logs crewai --tail=50
```

**Common causes:**
1. Ollama crashed → `docker compose restart ollama`
2. Weaviate down → `docker compose restart weaviate`
3. Out of memory → Restart Docker

---

## Ingestion Problems

### Issue: PDF Extraction Fails

**Symptoms:**
```
Failed to extract text from PDF: corrupted.pdf
```

**Solutions:**

**1. Verify PDF:**
```bash
# Try opening PDF manually
open data/raw/corrupted.pdf

# If corrupted, re-download or skip
```

**2. Skip problematic files:**
```bash
# Remove corrupted file
rm data/raw/corrupted.pdf

# Re-run ingestion
```

---

### Issue: ArXiv Download Fails

**Symptoms:**
```
Failed to download: 403 Forbidden
Failed to download: Connection timeout
```

**Solutions:**

**1. Check ArXiv status:**
Visit https://arxiv.org to see if it's accessible

**2. Retry later:**
ArXiv may be rate-limiting or under maintenance

**3. Use more specific queries:**
```bash
# Bad: Too broad
{"query": "AI"}

# Good: Specific
{"query": "transformer neural networks"}
```

---

### Issue: Duplicate Chunks

**Symptoms:**
```json
{
  "chunks_ingested": 0,
  "chunks_skipped": 150
}
```

**Cause:** Re-ingesting same documents

**Solution:**
```bash
# This is normal! Duplicates are automatically skipped
# If you want to re-ingest, reset the index first:

curl -X POST http://localhost:8000/rag/reset \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

---

## Docker Issues

### Issue: "docker: command not found"

**Solution:**
```bash
# Install Docker
# macOS: Download from docker.com
# Linux: 
curl -fsSL https://get.docker.com | sh

# Verify
docker --version
```

---

### Issue: Permission Denied (Linux)

**Symptoms:**
```
Got permission denied while trying to connect to Docker daemon
```

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in

# Verify
docker ps
```

---

### Issue: Container Keeps Restarting

**Symptoms:**
```
api      Restarting (1) 5 seconds ago
```

**Diagnosis:**
```bash
# Check exit code
docker compose ps

# View logs
docker compose logs api

# Common causes:
# - Missing environment variables
# - Port conflict
# - Dependency not ready
```

**Solutions:**

**1. Check environment:**
```bash
# Verify docker/.env exists and is complete
cat docker/.env
```

**2. Check dependencies:**
```bash
# Ensure Weaviate is healthy
docker compose ps weaviate

# Start services in order
docker compose up -d postgres weaviate ollama
sleep 10
docker compose up -d api crewai
```

---

## Network Problems

### Issue: Can't Access API from Host

**Symptoms:**
```
curl: (7) Failed to connect to localhost port 8000
```

**Diagnosis:**
```bash
# Check if API is running
docker compose ps api

# Check port mapping
docker compose port api 8000
```

**Solutions:**

**1. Verify port mapping:**
```bash
# Check docker-compose.yml
grep -A 5 "api:" docker/docker-compose.yml

# Should see:
# ports:
#   - "${API_PORT:-8000}:8000"
```

**2. Check firewall:**
```bash
# Windows: Allow through Windows Firewall
# macOS: System Preferences → Security
# Linux: sudo ufw allow 8000
```

---

### Issue: Services Can't Communicate

**Symptoms:**
```
Error: failed to connect to weaviate:8080
```

**Cause:** Using `localhost` instead of service names

**Solution:**

**❌ Wrong (in Docker containers):**
```python
WEAVIATE_URL = "http://localhost:8080"
```

**✅ Correct:**
```python
WEAVIATE_URL = "http://weaviate:8080"
```

---

## Data Issues

### Issue: Lost Data After Restart

**Cause:** Used `docker compose down -v` (deletes volumes)

**Prevention:**
```bash
# Stop without deleting volumes
docker compose down

# NOT this (deletes data):
# docker compose down -v
```

**Solution:**
Restore from backup (if available)

---

### Issue: Disk Full

**Symptoms:**
```
Error: no space left on device
```

**Diagnosis:**
```bash
# Check disk usage
df -h

# Check Docker usage
docker system df
```

**Solutions:**

**1. Clean Docker:**
```bash
# Remove unused containers/images
docker system prune -a

# Remove unused volumes
docker volume prune
```

**2. Clear logs:**
```bash
# Truncate logs
truncate -s 0 $(docker inspect --format='{{.LogPath}}' api)
```

**3. Free up space:**
```bash
# Remove old downloads
rm -rf data/arxiv/*

# Clear outputs
rm -rf outputs/*
```

---

## Getting More Help

### Check Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs api -f

# Last 100 lines
docker compose logs --tail=100 api

# Since timestamp
docker compose logs --since 2025-01-24T10:00:00
```

### Health Check Script
```bash
python scripts/admin/health_check.py
```

### Debug Mode
```bash
# Enable debug logging
# Edit docker/.env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart services
docker compose restart
```

### Report an Issue

If you can't find a solution:

1. **Check existing issues:**
   https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues

2. **Create new issue:**
   - Describe the problem
   - Include error messages
   - Attach logs: `docker compose logs > logs.txt`
   - Mention your OS and Docker version

3. **Ask in discussions:**
   https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/discussions

---

## Preventive Maintenance

### Regular Checks
```bash
# Weekly: Check disk space
df -h

# Weekly: Prune old Docker data
docker system prune

# Monthly: Update images
docker compose pull
docker compose up -d
```

### Backups
```bash
# Backup script
./scripts/admin/backup_data.sh

# Creates backup in backups/ directory
```

---

**[⬅ Back to Main README](../../README.md)**
```

---