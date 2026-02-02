# Command Reference

Quick reference for commonly used commands.

---

## 📋 Table of Contents

- [Docker Commands](#docker-commands)
- [Service Management](#service-management)
- [API Commands](#api-commands)
- [Database Commands](#database-commands)
- [Development Commands](#development-commands)
- [Troubleshooting Commands](#troubleshooting-commands)

---

## 🐳 Docker Commands

### Start Services
```bash
# Start all services
docker compose -f docker/docker-compose.yml up -d

# Start specific service
docker compose up -d api

# Start with GPU support
docker compose -f docker/docker-compose.yml -f docker/docker-compose.nvidia.yml up -d

# Start and view logs
docker compose up
```

### Stop Services
```bash
# Stop all services (keep data)
docker compose down

# Stop and remove volumes (delete data)
docker compose down -v

# Stop specific service
docker compose stop api
```

### Restart Services
```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart api

# Force recreate
docker compose up -d --force-recreate api
```

### View Status
```bash
# List running services
docker compose ps

# View service details
docker compose ps api

# Check health
docker compose ps --format json | jq
```

---

## 📊 Service Management

### View Logs
```bash
# All services (follow)
docker compose logs -f

# Specific service
docker compose logs api
docker compose logs ollama
docker compose logs weaviate

# Last N lines
docker compose logs --tail=100 api

# Since timestamp
docker compose logs --since 2025-02-02T10:00:00

# Multiple services
docker compose logs api crewai

# Search logs
docker compose logs api | grep -i error
docker compose logs api | grep -i "processing time"
```

### Execute Commands in Container
```bash
# Open shell in container
docker compose exec api bash
docker compose exec ollama sh

# Run single command
docker compose exec api python --version
docker compose exec postgres psql -U research_assistant

# As different user
docker compose exec -u root api bash
```

### Resource Usage
```bash
# Real-time stats
docker stats

# Specific container
docker stats api

# Once (no streaming)
docker stats --no-stream

# Format output
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## 🔌 API Commands

### Health Checks

**PowerShell**:
```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Readiness check
Invoke-RestMethod -Uri "http://localhost:8000/ready"

# Stats
Invoke-RestMethod -Uri "http://localhost:8000/rag/stats"
```

**Bash**:
```bash
# Health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Stats (formatted)
curl -s http://localhost:8000/rag/stats | jq
```

### Ingestion

**PowerShell**:
```powershell
# Ingest from ArXiv
$body = @{
    query = "machine learning"
    max_results = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# Ingest local files
$body = @{ pattern = "*" } | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/local" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Bash**:
```bash
# Ingest from ArXiv
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning","max_results":3}'

# Ingest local files
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern":"*"}'
```

### Query

**PowerShell**:
```powershell
# Research query
$body = @{
    query = "What is machine learning?"
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
# Research query
curl -X POST http://localhost:8000/research/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is machine learning?","language":"en"}' | jq -r '.answer'

# RAG query (no agents)
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query":"neural networks","top_k":5}' | jq
```

---

## 🗄️ Database Commands

### PostgreSQL
```bash
# Connect to database
docker compose exec postgres psql -U research_assistant -d research_assistant

# Backup database
docker compose exec postgres pg_dump -U research_assistant research_assistant > backup.sql

# Restore database
cat backup.sql | docker compose exec -T postgres psql -U research_assistant research_assistant

# List databases
docker compose exec postgres psql -U research_assistant -c "\l"

# List tables
docker compose exec postgres psql -U research_assistant -d research_assistant -c "\dt"

# Query
docker compose exec postgres psql -U research_assistant -d research_assistant -c "SELECT COUNT(*) FROM trulens_records;"
```

### Weaviate
```bash
# Get schema
curl http://localhost:8080/v1/schema | jq

# Get object count
curl http://localhost:8080/v1/objects?limit=0 | jq '.totalResults'

# Get meta info
curl http://localhost:8080/v1/meta | jq

# Query objects
curl -X POST http://localhost:8080/v1/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ Get { ResearchDocument(limit: 5) { content source } } }"}'

# Delete all objects (⚠️ dangerous)
curl -X DELETE http://localhost:8080/v1/objects?class=ResearchDocument
```

---

## 💻 Development Commands

### Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Update dependencies
pip freeze > requirements.txt
```

### Code Quality
```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Fix linting issues
ruff check src tests --fix

# Type check
mypy src

# All checks
black src tests && ruff check src tests --fix && mypy src
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_rag/test_processor.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run only fast tests (unit)
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run specific test
pytest tests/unit/test_rag/test_processor.py::test_chunk_id_deterministic -v
```

### Git
```bash
# Status
git status

# Add files
git add .
git add specific_file.py

# Commit (conventional commits)
git commit -m "feat(agents): add translator agent"
git commit -m "fix(rag): resolve connection timeout"
git commit -m "docs(api): update endpoint examples"

# Push
git push origin main

# Pull
git pull origin main

# Create branch
git checkout -b feature/my-feature

# View log
git log --oneline --graph
```

---

## 🔧 Troubleshooting Commands

### Check Services
```bash
# Health check script
python scripts/admin/health_check.py

# Check individual services
curl http://localhost:8000/health      # API
curl http://localhost:8080/v1/meta     # Weaviate
curl http://localhost:11434/api/tags   # Ollama
curl http://localhost:5678/healthz     # n8n
```

### Port Conflicts

**PowerShell**:
```powershell
# Check what's using a port
netstat -ano | findstr :8000

# Kill process by PID
taskkill /PID <PID> /F
```

**Bash**:
```bash
# Check what's using a port
lsof -i :8000

# Kill process by PID
kill -9 <PID>

# Kill by name
killall ollama
```

### Ollama
```bash
# List models
docker compose exec ollama ollama list

# Pull model
docker compose exec ollama ollama pull qwen3:1.7b

# Test model
docker compose exec ollama ollama run qwen3:1.7b "Hello, how are you?"

# Show model info
docker compose exec ollama ollama show qwen3:1.7b

# Delete model
docker compose exec ollama ollama rm qwen3:1.7b
```

### Disk Space
```bash
# Check Docker disk usage
docker system df

# Clean up
docker system prune
docker image prune
docker volume prune

# Remove unused volumes
docker volume ls
docker volume rm <volume_name>
```

### Network
```bash
# List networks
docker network ls

# Inspect network
docker network inspect research_net

# Test connectivity between containers
docker compose exec api ping weaviate
docker compose exec api ping ollama
```

---

## 🎯 Common Workflows

### Fresh Start
```bash
# 1. Stop everything
docker compose down -v

# 2. Pull latest images
docker compose pull

# 3. Rebuild images
docker compose build --no-cache

# 4. Start services
docker compose up -d

# 5. Check health
python scripts/admin/health_check.py

# 6. Ingest test data
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query":"test","max_results":1}'
```

### Update to Latest
```bash
# 1. Pull from git
git pull origin main

# 2. Stop services
docker compose down

# 3. Rebuild images
docker compose build

# 4. Start services
docker compose up -d

# 5. Verify
docker compose ps
```

### Backup Everything
```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup PostgreSQL
docker compose exec postgres pg_dump -U research_assistant research_assistant \
  > backups/$(date +%Y%m%d)/postgres.sql

# Backup environment files
cp .env backups/$(date +%Y%m%d)/
cp docker/.env backups/$(date +%Y%m%d)/

# Backup local data
tar -czf backups/$(date +%Y%m%d)/data.tar.gz data/

# List backups
ls -lh backups/
```

---

## 📚 Related Documentation

- **[Configuration Guide](CONFIGURATION.md)** - All settings
- **[Best Practices](BEST_PRACTICES.md)** - Optimization tips
- **[Troubleshooting](../setup/TROUBLESHOOTING.md)** - Common issues

---

**[⬅ Back to Guides](README.md)**