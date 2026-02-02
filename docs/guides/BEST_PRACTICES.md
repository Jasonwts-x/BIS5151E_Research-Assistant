# Best Practices & Optimization

Guidelines for optimal performance and quality.

---

## 📋 Table of Contents

- [Query Performance](#query-performance)
- [Ingestion Speed](#ingestion-speed)
- [Quality Optimization](#quality-optimization)
- [Resource Management](#resource-management)
- [Scaling](#scaling)
- [Monitoring](#monitoring)
- [Backup & Recovery](#backup--recovery)
- [Security](#security)

---

## ⚡ Query Performance

### Optimize Response Time

**Current**: ~28 seconds for full research query

**Target**: < 20 seconds

#### 1. Enable GPU Acceleration

**Impact**: 3-5x faster LLM inference
```bash
# See GPU setup guide
# Reduces LLM time from 25s to 6-8s
```

See: [GPU Setup Guide](../setup/GPU.md)

---

#### 2. Reduce Context Size
```bash
# .env
RAG_TOP_K=3              # Instead of 5 (default)
RAG_CHUNK_SIZE=250       # Instead of 350 (default)
```

**Impact**: -2 to -4 seconds

**Trade-off**: Slightly less context may reduce answer quality

---

#### 3. Use Faster Model
```bash
# .env
LLM_MODEL=qwen3:1.7b     # Already default (fastest)
LLM_MAX_TOKENS=1000      # Limit response length
```

**Impact**: -3 to -5 seconds

**Trade-off**: Shorter responses

---

#### 4. Optimize Ollama
```bash
# docker/.env
OLLAMA_KEEP_ALIVE=1h     # Keep model loaded longer
OLLAMA_NUM_PARALLEL=1    # Reduce overhead
```

**Impact**: -1 to -2 seconds (avoid model reloading)

---

### Expected Performance After Optimization

| Configuration | Time | Notes |
|---------------|------|-------|
| **Default (CPU)** | ~28s | Current baseline |
| **Optimized (CPU)** | ~18-20s | Reduced context + faster model |
| **GPU** | ~8-10s | GPU acceleration |
| **GPU + Optimized** | ~6-8s | Best performance |

---

## 📥 Ingestion Speed

### Optimize Ingestion

**Current**: ~30-60 seconds for 3 papers

#### 1. GPU Acceleration
```bash
# Enable GPU for embeddings (future feature)
# Currently only LLM uses GPU
```

**Impact**: 50% faster embedding generation

---

#### 2. Parallel Processing (Future)
```python
# Currently sequential, future enhancement
# Download multiple PDFs in parallel
```

---

#### 3. Reduce Papers per Batch
```bash
# Instead of ingesting 10 papers at once:
# Ingest 3 papers, query, then ingest more if needed
```

**Impact**: Faster feedback, better user experience

---

#### 4. Local Files vs ArXiv

**Local files** are faster (no download):
- ArXiv: 30-60s for 3 papers
- Local: 10-20s for 3 papers

**Recommendation**: Pre-download papers for repeated experiments

---

## 🎯 Quality Optimization

### Improve Answer Quality

#### 1. Increase Context
```bash
# .env
RAG_TOP_K=10             # More chunks (default: 5)
RAG_CHUNK_SIZE=500       # Larger chunks (default: 350)
```

**Impact**: More comprehensive answers

**Trade-off**: +5 to +10 seconds processing time

---

#### 2. Better Model
```bash
# .env
LLM_MODEL=qwen3:4b       # Better quality (default: qwen3:1.7b)
LLM_MAX_TOKENS=4096      # Longer responses
```

**Impact**: Higher quality answers

**Trade-off**: +10 to +15 seconds processing time

---

#### 3. Lower Temperature
```bash
# .env
LLM_TEMPERATURE=0.1      # More factual (default: 0.3)
```

**Impact**: More consistent, factual responses

**Trade-off**: Less creative

---

#### 4. Tune Retrieval

**For keyword-heavy queries** (technical terms):
```bash
RAG_ALPHA=0.3            # Favor BM25 keyword search
```

**For concept-heavy queries** (abstract ideas):
```bash
RAG_ALPHA=0.7            # Favor vector semantic search
```

---

#### 5. Quality Data

**Ingest high-quality sources**:
- Peer-reviewed papers (ArXiv)
- Well-written documents
- Relevant to your domain

**Avoid**:
- Low-quality OCR text
- Heavily formatted documents
- Irrelevant papers

---

### Improve Citation Quality

#### 1. Enable Strict Validation
```bash
# .env
GUARDRAILS_CITATION_REQUIRED=true
GUARDRAILS_STRICT_MODE=true
```

---

#### 2. Review FactChecker Agent

Edit `src/agents/api/crew.py`:
```python
factchecker = Agent(
    role="Fact Validator",
    goal="Verify EVERY claim is supported by context with proper citation",
    # Emphasize citation importance in prompt
    ...
)
```

---

## 💾 Resource Management

### Memory Optimization

#### Monitor Memory Usage
```bash
# Real-time monitoring
docker stats

# Check specific service
docker stats ollama
```

---

#### Reduce Memory Usage

**Ollama**:
```bash
# docker/.env
OLLAMA_NUM_PARALLEL=1         # Reduce parallel requests
OLLAMA_MAX_LOADED_MODELS=1    # Keep only 1 model loaded
OLLAMA_KEEP_ALIVE=5m          # Unload model faster
```

**Weaviate**:
```yaml
# docker-compose.yml
services:
  weaviate:
    deploy:
      resources:
        limits:
          memory: 2G          # Limit Weaviate memory
```

---

### Disk Space Management

#### Monitor Disk Usage
```bash
# Docker disk usage
docker system df

# Service-specific
docker system df -v
```

---

#### Clean Up
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused build cache
docker builder prune

# Full cleanup (⚠️ careful!)
docker system prune -a --volumes
```

---

#### Backup Before Cleanup
```bash
# Backup data before pruning volumes
./scripts/admin/backup.sh
```

---

### CPU Optimization

#### Limit CPU Usage
```yaml
# docker-compose.yml
services:
  ollama:
    deploy:
      resources:
        limits:
          cpus: '4.0'         # Max 4 cores
```

---

#### Parallel Processing
```bash
# docker/.env
OLLAMA_NUM_PARALLEL=2         # Process 2 requests at once
```

**Trade-off**: Higher throughput, more resource usage

---

## 📈 Scaling

### Vertical Scaling (Single Machine)

#### Add More Resources

**Docker Desktop**:
1. Settings → Resources
2. Increase CPU: 8+ cores
3. Increase Memory: 16GB+
4. Increase Disk: 50GB+

**Linux**:
- Resources automatically available
- Adjust per-service limits in `docker-compose.yml`

---

#### GPU Acceleration

See [GPU Setup](../setup/GPU.md)

**Benefits**:
- 3-5x faster inference
- Handle more queries
- Better quality with larger models

---

### Horizontal Scaling (Future)

**Planned** (v2.1.0):
- Multiple API instances behind load balancer
- CrewAI worker pool
- Weaviate replication
- PostgreSQL read replicas

---

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test API
ab -n 100 -c 10 http://localhost:8000/health

# Test query endpoint (limited by Ollama)
ab -n 10 -c 1 -p query.json -T application/json http://localhost:8000/rag/query
```

---

## 📊 Monitoring

### Health Monitoring

#### Automated Health Checks
```bash
# Run health check script
python scripts/admin/health_check.py

# Schedule with cron (Linux)
*/5 * * * * python /path/to/scripts/admin/health_check.py >> /var/log/health.log
```

---

#### Manual Checks
```bash
# API health
curl http://localhost:8000/health

# Readiness (checks dependencies)
curl http://localhost:8000/ready

# Service stats
curl http://localhost:8000/rag/stats
```

---

### Performance Monitoring

#### Docker Stats
```bash
# Real-time stats
docker stats

# Log to file
docker stats --no-stream >> stats.log
```

---

#### Query Timing

**Enable performance tracking**:
```bash
# .env
EVAL_ENABLE_PERFORMANCE=true
```

**View logs**:
```bash
docker compose logs api | grep "processing_time"
```

---

### Log Monitoring

#### Structured Logging
```bash
# All logs
docker compose logs -f

# Error logs only
docker compose logs api | grep ERROR

# Performance logs
docker compose logs api | grep "processing_time\|metric"
```

---

#### Log Rotation

**Docker log limits** (`docker-compose.yml`):
```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

### Metrics Dashboard (Future)

**Planned** (v1.2.0):
- Prometheus metrics export
- Grafana dashboards
- Real-time visualization

---

## 💾 Backup & Recovery

### Regular Backups

#### Automated Backup Script
```bash
#!/bin/bash
# scripts/admin/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/$DATE"

mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
docker compose exec -T postgres pg_dump -U research_assistant research_assistant \
  > "$BACKUP_DIR/postgres.sql"

# Backup environment files
cp .env "$BACKUP_DIR/"
cp docker/.env "$BACKUP_DIR/"

# Backup local data
tar -czf "$BACKUP_DIR/data.tar.gz" data/

echo "✅ Backup completed: $BACKUP_DIR"
```

**Schedule**:
```bash
# Daily at 2 AM
0 2 * * * /path/to/scripts/admin/backup.sh
```

---

### Recovery

#### Restore PostgreSQL
```bash
# Stop services
docker compose down

# Start PostgreSQL only
docker compose up -d postgres

# Restore database
cat backups/20250202/postgres.sql | \
  docker compose exec -T postgres psql -U research_assistant research_assistant

# Restart all services
docker compose up -d
```

---

#### Restore Weaviate

**Weaviate data is in volume**:
```bash
# Backup volume
docker run --rm -v research-assistant_weaviate_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/weaviate_backup.tar.gz /data

# Restore volume
docker run --rm -v research-assistant_weaviate_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/weaviate_backup.tar.gz -C /
```

**Or**: Re-ingest documents (easier)

---

## 🔐 Security

### Current Security Model

**Local deployment** (trusted environment):
- No authentication
- No encryption
- Localhost only

**Suitable for**:
- Personal use
- Academic research
- Development

---

### Production Security (Future)

**Planned** (v3.1.0):
- JWT authentication
- API key management
- HTTPS/TLS
- Rate limiting
- RBAC (role-based access control)

---

### Current Best Practices

#### 1. Network Isolation
```bash
# Bind to localhost only (default)
# Don't expose to internet

# If needed, use firewall
sudo ufw allow from 192.168.1.0/24 to any port 8000
```

---

#### 2. Strong Passwords
```bash
# docker/.env
POSTGRES_PASSWORD=$(openssl rand -base64 32)
N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
```

---

#### 3. Regular Updates
```bash
# Update Docker images
docker compose pull

# Update application
git pull origin main
docker compose build
```

---

#### 4. Input Validation

**Already enabled** (Guardrails):
- Query length limits
- Jailbreak detection
- PII detection
- Content safety

---

## 📚 Summary Checklist

### Daily Operations

- [ ] Check service health: `docker compose ps`
- [ ] Monitor logs: `docker compose logs --tail=50`
- [ ] Check disk space: `docker system df`

### Weekly Tasks

- [ ] Review query performance logs
- [ ] Check resource usage: `docker stats --no-stream`
- [ ] Clean up old data: `docker system prune`

### Monthly Tasks

- [ ] Backup databases and data
- [ ] Review and archive old documents
- [ ] Update Docker images
- [ ] Check for security updates

---

## 📚 Related Documentation

- **[Configuration Guide](CONFIGURATION.md)** - All settings
- **[Command Reference](COMMAND_REFERENCE.md)** - Common commands
- **[Troubleshooting](../setup/TROUBLESHOOTING.md)** - Common issues

---

**[⬅ Back to Guides](README.md)**