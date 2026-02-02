# Troubleshooting Guide

Common issues and solutions for ResearchAssistantGPT.

---

## 📋 Quick Diagnostic Commands

Run these first to diagnose issues:
```bash
# Check service status
docker compose ps

# Check service health
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8080/v1/meta
curl http://localhost:11434/api/tags

# View logs
docker compose logs --tail=50

# View specific service logs
docker compose logs api
docker compose logs weaviate
docker compose logs ollama
docker compose logs n8n
```

---

## 🚫 Common Startup Issues

### Issue 1: Ollama Desktop App Blocking Port 11434

**Symptoms**:
- API logs show: `Failed to connect to Ollama at http://ollama:11434`
- Ollama container fails to start with port conflict

**Cause**: Ollama desktop application is running and blocking port 11434.

**Solution**:

**Windows**:
1. Look for Ollama icon in system tray (bottom-right)
2. Right-click icon
3. Click **"Quit Ollama"**

**macOS**:
1. Look for Ollama icon in menu bar (top-right)
2. Click icon
3. Click **"Quit Ollama"**

**Linux**:
```bash
# Kill Ollama process
killall ollama

# Or find and kill specifically
ps aux | grep ollama
kill -9 <PID>
```

**Prevent in future**:
- **Windows**: Task Manager → Startup → Disable Ollama
- **macOS**: System Preferences → Users & Groups → Login Items → Remove Ollama
- **Linux**: Remove from autostart applications

**Then restart Docker services**:
```bash
docker compose restart ollama api crewai
```

---

### Issue 2: Port Already in Use

**Symptoms**:
- Error: `Bind for 0.0.0.0:8000 failed: port is already allocated`
- Container fails to start

**Cause**: Another application is using the port.

**Solution**:

**Find what's using the port**:
```powershell
# Windows PowerShell
netstat -ano | findstr :8000
# Note the PID (last column)

# Kill the process
taskkill /PID <PID> /F
```
```bash
# Linux/macOS
lsof -i :8000
# Note the PID

# Kill the process
kill -9 <PID>
```

**Or change the port**:

Edit `docker/.env`:
```env
API_PORT=9000  # Change from 8000 to 9000
```

Then restart:
```bash
docker compose down
docker compose up -d
```

**Common port conflicts**:
| Port | Service | Alternative |
|------|---------|-------------|
| 8000 | API | 9000 |
| 5678 | n8n | 5679 |
| 8080 | Weaviate | 8081 |
| 11434 | Ollama | 11435 |

---

### Issue 3: Services Fail to Start (Out of Memory)

**Symptoms**:
- Services crash randomly
- Docker Desktop shows high memory usage
- Logs show: `Killed` or `Out of memory`

**Cause**: Docker doesn't have enough memory allocated.

**Solution**:

**Increase Docker memory allocation**:

1. Open **Docker Desktop**
2. Go to **Settings** → **Resources**
3. Increase **Memory**:
   - Minimum: **8GB**
   - Recommended: **16GB**
4. Click **"Apply & Restart"**

**Reduce service memory usage**:

Edit `docker-compose.yml` to limit Ollama:
```yaml
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 4G  # Reduce from 6G
```

---

### Issue 4: Weaviate Connection Refused

**Symptoms**:
- API logs show: `ConnectionError: Failed to connect to Weaviate`
- `/ready` endpoint returns `weaviate_ok: false`

**Cause**: Weaviate hasn't finished starting or crashed.

**Solution**:

**Check Weaviate status**:
```bash
docker compose logs weaviate

# Should see: "Serving weaviate at http://[::]:8080"
```

**Restart Weaviate**:
```bash
docker compose restart weaviate

# Wait 30 seconds
sleep 30

# Check again
curl http://localhost:8080/v1/meta
```

**If still fails, recreate Weaviate volume**:
```bash
# ⚠️ WARNING: This deletes all ingested documents
docker compose down
docker volume rm research-assistant_weaviate_data
docker compose up -d weaviate

# Wait for Weaviate to initialize
docker compose logs -f weaviate
# Press Ctrl+C when you see "Serving weaviate..."
```

---

### Issue 5: Ollama Model Not Found

**Symptoms**:
- Error: `Model 'qwen3:1.7b' not found`
- CrewAI logs show model errors
- Query responses: `Failed to generate completion`

**Cause**: Ollama model not downloaded or download failed.

**Solution**:

**Check available models**:
```bash
docker compose exec ollama ollama list
```

**Expected output**:
```
NAME              ID              SIZE
qwen3:1.7b        abc123def       1.0GB
qwen3:4b          def456ghi       2.4GB
```

**Pull missing model**:
```bash
docker compose exec ollama ollama pull qwen3:1.7b

# Expected output:
# pulling manifest
# pulling abc123def... 100%
# verifying sha256 digest
# writing manifest
# success
```

**Pull all configured models**:
```bash
docker compose exec ollama ollama pull qwen3:1.7b
docker compose exec ollama ollama pull qwen3:4b
docker compose exec ollama ollama pull qwen2.5:3b
docker compose exec ollama ollama pull llama3.2:3b
```

**Verify**:
```bash
docker compose exec ollama ollama list
```

---

### Issue 6: n8n Database Connection Error

**Symptoms**:
- n8n fails to start
- Logs show: `Connection to database failed`
- Error: `FATAL: password authentication failed`

**Cause**: PostgreSQL password mismatch between `docker/.env` and n8n configuration.

**Solution**:

**Check password is set in `docker/.env`**:
```bash
cat docker/.env | grep POSTGRES_PASSWORD
```

Should show:
```env
POSTGRES_PASSWORD=your_password_here
```

**If missing, set it**:
```env
# docker/.env
POSTGRES_PASSWORD=your_secure_password_here
```

**Restart services**:
```bash
docker compose restart postgres n8n

# Wait for both to be healthy
docker compose ps
```

**If still fails, recreate database**:
```bash
# ⚠️ WARNING: This deletes n8n workflows
docker compose down
docker volume rm research-assistant_postgres_data
docker compose up -d postgres n8n
```

---

## 🔍 Service-Specific Issues

### API Service

#### Issue: API returns 503 Service Unavailable

**Cause**: Weaviate or Ollama not ready.

**Solution**:
```bash
# Check dependencies
curl http://localhost:8080/v1/meta  # Weaviate
curl http://localhost:11434/api/tags  # Ollama

# Restart API after dependencies are ready
docker compose restart api
```

#### Issue: API returns 500 Internal Server Error

**Solution**:
```bash
# Check API logs for detailed error
docker compose logs api --tail=100

# Common causes:
# 1. Weaviate connection issue → Restart Weaviate
# 2. Ollama model issue → Pull model
# 3. Code error → Check logs for stack trace
```

---

### Weaviate

#### Issue: Weaviate keeps restarting

**Solution**:
```bash
# Check logs
docker compose logs weaviate

# Common causes:
# 1. Corrupted data → Remove volume
# 2. Out of memory → Increase Docker memory
# 3. Port conflict → Change WEAVIATE_PORT in docker/.env
```

#### Issue: Schema errors

**Solution**:
```bash
# Reset schema (⚠️ deletes all data)
docker compose exec api python -c "
from src.rag.core.pipeline import get_rag_pipeline
pipeline = get_rag_pipeline()
# Schema will be recreated on next ingestion
"
```

---

### Ollama

#### Issue: Ollama is slow

**Possible causes**:
1. Running on CPU (no GPU)
2. Model too large for available resources
3. Multiple models loaded

**Solution**:
```bash
# 1. Enable GPU (if available)
# See: docs/setup/GPU.md

# 2. Use smaller model
# Edit docker/.env
OLLAMA_MODEL=qwen3:1.7b  # Fastest

# 3. Limit loaded models
# Edit docker/.env
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_NUM_PARALLEL=1
```

#### Issue: Ollama uses too much memory

**Solution**:
```bash
# Edit docker-compose.yml
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 4G  # Reduce from 6G
```

---

### n8n

#### Issue: Workflow execution fails

**Solution**:
1. Check **Executions** panel in n8n
2. Click on failed execution
3. View error in failed node
4. Common issues:
   - Wrong URL (use `http://api:8000`, not `localhost:8000`)
   - Timeout (increase to 60000ms in HTTP node options)
   - API service down (check `docker compose ps`)

#### Issue: Can't access n8n at localhost:5678

**Solution**:
```bash
# Check n8n is running
docker compose ps n8n

# Check logs
docker compose logs n8n

# Restart n8n
docker compose restart n8n
```

---

## 🐛 Query Issues

### Issue: "No documents found" when querying

**Cause**: Index is empty (no documents ingested).

**Solution**:
```bash
# Check index status
curl http://localhost:8000/rag/stats
```

Expected: `{"total_documents": 10, ...}`

If `total_documents: 0`, ingest some papers:
```powershell
# PowerShell
$body = @{
    query = "machine learning"
    max_results = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

### Issue: Query times out

**Cause**: Query takes >60 seconds (default timeout).

**Solution**:

**Reduce query time**:
1. Use fewer papers (`max_results: 3` instead of 10)
2. Use smaller model (qwen3:1.7b)
3. Enable GPU acceleration

**Increase timeout** (temporary):
```bash
# Edit .env
API_TIMEOUT=120  # Increase to 120 seconds
```

---

### Issue: Poor quality results

**Cause**: Retrieval returning irrelevant chunks.

**Solution**:

**Adjust RAG parameters**:
```bash
# Edit .env
RAG_TOP_K=10  # Retrieve more chunks (default: 5)
RAG_ALPHA=0.7  # Favor vector search over BM25 (default: 0.5)
```

**Improve document quality**:
- Ingest more specific papers
- Use more targeted ArXiv queries
- Filter low-quality documents

---

## 🔧 Docker Issues

### Issue: "docker compose" command not found

**Cause**: Old Docker version.

**Solution**:

**Check Docker version**:
```bash
docker --version
# Should be 20.10+ with Docker Compose V2
```

**If old version**:
```bash
# Use old syntax
docker-compose -f docker/docker-compose.yml up -d

# Or update Docker Desktop
```

---

### Issue: Permission denied errors (Linux)

**Cause**: Docker requires sudo, but you're running without it.

**Solution**:

**Add user to docker group**:
```bash
sudo usermod -aG docker $USER
newgrp docker

# Test
docker ps
```

---

### Issue: Volumes persist old data after rebuild

**Cause**: Named volumes not removed.

**Solution**:

**List volumes**:
```bash
docker volume ls
```

**Remove project volumes** (⚠️ deletes all data):
```bash
docker compose down -v

# Or manually
docker volume rm research-assistant_postgres_data
docker volume rm research-assistant_weaviate_data
docker volume rm research-assistant_ollama_data
docker volume rm research-assistant_n8n_data
```

**Then rebuild**:
```bash
docker compose up -d
```

---

## 📊 Performance Issues

### Issue: High CPU usage

**Common causes**:
1. Multiple Ollama requests at once
2. Large documents being embedded
3. Weaviate indexing

**Solution**:
```bash
# Limit Ollama parallelism
# Edit docker/.env
OLLAMA_NUM_PARALLEL=1

# Check what's using CPU
docker stats
```

---

### Issue: Disk space filling up

**Cause**: Docker images, volumes, and build cache.

**Solution**:

**Check disk usage**:
```bash
docker system df
```

**Clean up**:
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove build cache
docker builder prune

# Full cleanup (⚠️ careful!)
docker system prune -a --volumes
```

---

## 🆘 Emergency Procedures

### Complete Reset

If nothing works, reset everything:
```bash
# 1. Stop all services
docker compose down

# 2. Remove all volumes (⚠️ deletes ALL data)
docker volume rm research-assistant_postgres_data
docker volume rm research-assistant_weaviate_data
docker volume rm research-assistant_ollama_data
docker volume rm research-assistant_n8n_data

# 3. Remove all images
docker rmi $(docker images -q research-assistant*)

# 4. Start fresh
docker compose up -d

# 5. Wait for services to initialize (3-5 minutes)
docker compose logs -f
```

---

### Backup Before Reset

**Backup databases**:
```bash
# PostgreSQL
docker compose exec postgres pg_dump -U research_assistant research_assistant > backup_postgres.sql

# Can't easily backup Weaviate, but can re-ingest papers
```

**Restore**:
```bash
# After reset, restore PostgreSQL
cat backup_postgres.sql | docker compose exec -T postgres psql -U research_assistant research_assistant
```

---

## 📞 Getting Help

### 1. Check Documentation
- [Installation Guide](INSTALLATION.md)
- [API Documentation](../api/README.md)
- [Setup README](README.md)

### 2. Search GitHub Issues
https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues

### 3. Ask for Help
- **Discussions**: https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/discussions
- **New Issue**: https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues/new

### 4. Provide Diagnostic Info

When asking for help, include:
```bash
# System info
uname -a  # Linux/macOS
systeminfo  # Windows

# Docker version
docker --version
docker compose version

# Service status
docker compose ps

# Service logs (last 100 lines)
docker compose logs --tail=100 > logs.txt

# Environment (redact passwords!)
cat .env
cat docker/.env
```

---

**[⬅ Back to Setup Guide](README.md)** | **[⬆ Back to Installation](INSTALLATION.md)**