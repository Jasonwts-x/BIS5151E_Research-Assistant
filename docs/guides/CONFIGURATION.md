# Configuration Guide

Complete reference for all configuration options.

---

## 📋 Table of Contents

- [Environment Files](#environment-files)
- [Application Settings](#application-settings)
- [Docker Settings](#docker-settings)
- [RAG Parameters](#rag-parameters)
- [Agent Configuration](#agent-configuration)
- [Evaluation Settings](#evaluation-settings)

---

## 📁 Environment Files

### `.env` (Application Configuration)

**Location**: Repository root

**Purpose**: Application-level settings (RAG, LLM, evaluation)

**Optional**: Yes (defaults work for most users)
```bash
# Copy example
cp .env.example .env
```

---

### `docker/.env` (Docker Configuration)

**Location**: `docker/.env`

**Purpose**: Docker service settings (ports, passwords, credentials)

**Required**: Yes (must set passwords and keys)
```bash
# Copy example
cp docker/.env.example docker/.env

# Edit and set required values
nano docker/.env
```

**Required Values**:
```bash
POSTGRES_PASSWORD=your_secure_password_here
N8N_ENCRYPTION_KEY=your_64_character_hex_key_here
```

---

## ⚙️ Application Settings

### LLM Configuration
```bash
# .env

# Model Selection
LLM_MODEL=qwen3:1.7b              # Default model (fast, good quality)
# Options:
# - qwen3:1.7b   (1.7B params, fastest, 1GB)
# - qwen3:4b     (4B params, balanced, 2.4GB)
# - qwen2.5:3b   (3B params, alternative, 1.9GB)
# - llama3.2:3b  (3B params, Meta model, 2.0GB)

# Ollama Connection
OLLAMA_HOST=http://ollama:11434   # Ollama service URL
OLLAMA_TIMEOUT=300                # Request timeout (seconds)

# Generation Parameters
LLM_TEMPERATURE=0.3               # Randomness (0.0-1.0)
# Lower = more deterministic
# Higher = more creative
LLM_MAX_TOKENS=2048               # Max response length
```

**When to Change**:
- Use `qwen3:4b` for better quality (slower)
- Lower temperature (0.1-0.2) for factual responses
- Higher temperature (0.5-0.7) for creative writing

---

### RAG Configuration
```bash
# .env

# Weaviate Connection
WEAVIATE_URL=http://weaviate:8080  # Vector database URL

# Chunking Parameters
RAG_CHUNK_SIZE=350                 # Characters per chunk
RAG_CHUNK_OVERLAP=50               # Overlap between chunks

# Retrieval Parameters
RAG_TOP_K=5                        # Number of chunks to retrieve
RAG_ALPHA=0.5                      # Hybrid search weight (0.0-1.0)
# 0.0 = pure BM25 (keyword)
# 0.5 = balanced
# 1.0 = pure vector (semantic)

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# Fast, good quality, 384 dimensions
```

**Tuning Guide**:

**Chunk Size**:
- **Smaller (200-300)**: More precise, more chunks, slower
- **Medium (350-500)**: Balanced (current default)
- **Larger (600-1000)**: More context per chunk, fewer chunks

**Top-K**:
- **Low (3-5)**: Focused context, faster, risk missing info
- **Medium (5-10)**: Balanced (current default)
- **High (10-20)**: Comprehensive, slower, more noise

**Alpha (Vector Weight)**:
- **Low (0.2-0.4)**: Favor keywords (good for specific terms)
- **Medium (0.5)**: Balanced (current default)
- **High (0.6-0.8)**: Favor meaning (good for concepts)

---

### Development Settings
```bash
# .env

# Schema Management
ALLOW_SCHEMA_RESET=true            # Allow /rag/reset endpoint
# Set to false in production

# Logging
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR
# DEBUG for development
# INFO for production

# API Settings
API_TIMEOUT=60                     # Request timeout (seconds)
```

---

## 🐳 Docker Settings

### Service Ports
```bash
# docker/.env

# External Ports (mapped to host)
API_PORT=8000                      # API gateway
CREWAI_PORT=8100                   # CrewAI service
N8N_PORT=5678                      # n8n workflow UI
WEAVIATE_PORT=8080                 # Weaviate API
OLLAMA_PORT=11434                  # Ollama API
POSTGRES_PORT=5432                 # PostgreSQL
```

**Change if ports conflict**:
```bash
# Example: API port conflict
API_PORT=9000                      # Use 9000 instead of 8000
```

---

### Database Configuration
```bash
# docker/.env

# PostgreSQL (Required)
POSTGRES_DB=research_assistant     # Database name
POSTGRES_USER=research_assistant   # Database user
POSTGRES_PASSWORD=your_password    # ⚠️ MUST SET THIS

# n8n Encryption (Required)
N8N_ENCRYPTION_KEY=your_hex_key    # ⚠️ MUST SET THIS (64 chars)
# Generate with:
# Linux/macOS: openssl rand -hex 32
# Windows: -join ((0..31) | ForEach-Object { "{0:X2}" -f (Get-Random -Maximum 256) })
```

---

### Ollama Configuration
```bash
# docker/.env

# Model to Pull
OLLAMA_MODEL=qwen3:1.7b            # Model to download on init

# Performance Settings
OLLAMA_NUM_PARALLEL=1              # Concurrent requests (1-4)
OLLAMA_MAX_LOADED_MODELS=1         # Models in memory (1-2)
OLLAMA_KEEP_ALIVE=30m              # Keep model loaded (5m-2h)

# GPU Settings (if using GPU)
OLLAMA_GPU_LAYERS=-1               # GPU layers (-1 = auto, 0 = CPU)
```

**Resource Trade-offs**:

**OLLAMA_NUM_PARALLEL**:
- `1`: Sequential processing, less memory
- `2-4`: Parallel processing, more memory, faster throughput

**OLLAMA_KEEP_ALIVE**:
- `5m`: Save memory, slower first query after idle
- `30m`: Balanced (default)
- `2h`: Always ready, uses 1-2GB RAM constantly

---

### n8n Configuration
```bash
# docker/.env

# n8n Settings
N8N_HOST=localhost                 # Hostname
N8N_PORT=5678                      # Port
N8N_PROTOCOL=http                  # http or https
WEBHOOK_URL=http://localhost:5678/ # Webhook base URL

# Timezone
GENERIC_TIMEZONE=Europe/Berlin     # Your timezone
# Examples: America/New_York, Asia/Tokyo, UTC
```

---

## 🎛️ RAG Parameters

### Performance vs Quality

**Fast (Low Latency)**:
```bash
RAG_CHUNK_SIZE=250
RAG_TOP_K=3
LLM_MODEL=qwen3:1.7b
LLM_MAX_TOKENS=500
```

**Balanced** (Current Default):
```bash
RAG_CHUNK_SIZE=350
RAG_TOP_K=5
LLM_MODEL=qwen3:1.7b
LLM_MAX_TOKENS=2048
```

**Quality (High Accuracy)**:
```bash
RAG_CHUNK_SIZE=500
RAG_TOP_K=10
LLM_MODEL=qwen3:4b
LLM_MAX_TOKENS=4096
```

---

### Language-Specific Settings

**English (Technical)**:
```bash
RAG_ALPHA=0.4        # Favor keywords
LLM_TEMPERATURE=0.2  # More deterministic
```

**English (General)**:
```bash
RAG_ALPHA=0.5        # Balanced
LLM_TEMPERATURE=0.3  # Slightly creative
```

**Multilingual**:
```bash
RAG_ALPHA=0.6        # Favor semantics
LLM_TEMPERATURE=0.3  # Balanced creativity
```

---

## 🤖 Agent Configuration

### Agent Parameters

**Defined in code** (`src/agents/api/crew.py`):
```python
# Writer Agent
writer = Agent(
    role="Research Writer",
    goal="Write clear, concise summaries...",
    backstory="...",
    llm=llm,
    verbose=True
)

# Reviewer Agent
reviewer = Agent(
    role="Content Reviewer",
    goal="Improve clarity and grammar...",
    backstory="...",
    llm=llm,
    verbose=True
)

# FactChecker Agent
factchecker = Agent(
    role="Fact Validator",
    goal="Verify claims are supported...",
    backstory="...",
    llm=llm,
    verbose=True
)
```

**Customization** (edit `src/agents/api/crew.py`):
```python
# Modify agent behavior
writer = Agent(
    role="Research Writer",
    goal="Your custom goal",
    backstory="Your custom backstory",
    llm=llm,
    verbose=True,
    max_iter=5,              # Max iterations
    allow_delegation=False   # Allow delegation to other agents
)
```

---

## 🛡️ Evaluation Settings

### Guardrails
```bash
# .env

# Citation Validation
GUARDRAILS_CITATION_REQUIRED=true  # Require citations in output
# true: Strict (reject if missing)
# false: Lenient (warn only)

# Validation Mode
GUARDRAILS_STRICT_MODE=false       # Strict validation
# true: Reject on warnings
# false: Warn but allow (development)
```

**Use Cases**:

**Development**:
```bash
GUARDRAILS_CITATION_REQUIRED=true
GUARDRAILS_STRICT_MODE=false
```

**Production**:
```bash
GUARDRAILS_CITATION_REQUIRED=true
GUARDRAILS_STRICT_MODE=true
```

---

### TruLens
```bash
# .env

# TruLens Evaluation
EVAL_ENABLE_TRULENS=true           # Enable TruLens metrics
EVAL_FAITHFULNESS_METRIC=trulens_groundedness

# Performance Tracking
EVAL_ENABLE_PERFORMANCE=true       # Track timing metrics
```

---

## 📊 Resource Limits

### Docker Resource Allocation

**Edit `docker-compose.yml`**:
```yaml
services:
  ollama:
    deploy:
      resources:
        limits:
          cpus: '4.0'           # Max CPUs
          memory: 6G            # Max memory
        reservations:
          cpus: '2.0'           # Reserved CPUs
          memory: 4G            # Reserved memory
```

**Recommended Limits**:

| Service | CPU | Memory | Notes |
|---------|-----|--------|-------|
| **api** | 2 | 2G | Lightweight |
| **crewai** | 2 | 2G | Lightweight |
| **ollama** | 4+ | 6G | CPU-intensive |
| **weaviate** | 2 | 4G | Memory for vectors |
| **postgres** | 1 | 1G | Small database |
| **n8n** | 1 | 512M | Minimal |

---

## 🔧 Advanced Configuration

### Custom Embedding Model
```bash
# .env
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
# Multilingual model, 384 dimensions

# Or
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
# Higher quality, 768 dimensions, slower
```

---

### Custom LLM Endpoint
```bash
# .env
OLLAMA_HOST=http://custom-ollama-server:11434
# Point to different Ollama instance
```

---

### Custom Weaviate Schema

Edit `src/rag/core/schema.py`:
```python
SCHEMA = {
    "class": "ResearchDocument",
    "properties": [
        # ... existing properties
        {
            "name": "custom_field",
            "dataType": ["text"],
            "description": "Your custom field"
        }
    ]
}
```

---

## 🔄 Configuration Reload

### Which Settings Require Restart?

**Requires container restart**:
- Docker ports (`docker/.env`)
- Ollama settings (`OLLAMA_*`)
- Database passwords
- Resource limits
```bash
docker compose restart
```

**Requires service restart**:
- RAG parameters (`RAG_*`)
- LLM settings (`LLM_*`)
- Evaluation settings (`EVAL_*`)
```bash
docker compose restart api crewai
```

**No restart required**:
- Some agent prompts (reloaded per request)
- Query parameters (per-request)

---

## 📚 Configuration Examples

### Local Development
```bash
# .env
LOG_LEVEL=DEBUG
ALLOW_SCHEMA_RESET=true
GUARDRAILS_STRICT_MODE=false
EVAL_ENABLE_TRULENS=true

# docker/.env
API_PORT=8000
OLLAMA_KEEP_ALIVE=2h
```

---

### Production
```bash
# .env
LOG_LEVEL=INFO
ALLOW_SCHEMA_RESET=false
GUARDRAILS_STRICT_MODE=true
EVAL_ENABLE_TRULENS=true

# docker/.env
# Strong passwords
POSTGRES_PASSWORD=<strong-random-password>
N8N_ENCRYPTION_KEY=<64-char-hex-key>

# Conservative resources
OLLAMA_NUM_PARALLEL=1
OLLAMA_KEEP_ALIVE=30m
```

---

### High Performance
```bash
# .env
RAG_TOP_K=3
RAG_CHUNK_SIZE=250
LLM_MODEL=qwen3:1.7b
LLM_MAX_TOKENS=1000

# docker/.env
OLLAMA_NUM_PARALLEL=2
OLLAMA_MAX_LOADED_MODELS=2
OLLAMA_KEEP_ALIVE=1h
```

**Also**: Enable GPU (see [GPU Setup](../setup/GPU.md))

---

### High Quality
```bash
# .env
RAG_TOP_K=10
RAG_CHUNK_SIZE=500
LLM_MODEL=qwen3:4b
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.2

# docker/.env
OLLAMA_KEEP_ALIVE=2h
```

---

## 📝 Configuration Validation

### Check Configuration
```bash
# Verify environment files exist
ls -la .env docker/.env

# Check required variables are set
grep -E "POSTGRES_PASSWORD|N8N_ENCRYPTION_KEY" docker/.env

# Test configuration
docker compose config

# Validate and start
docker compose up --dry-run
```

---

## 📚 Related Documentation

- **[Setup Guide](../setup/INSTALLATION.md)** - Installation
- **[Best Practices](BEST_PRACTICES.md)** - Optimization
- **[Command Reference](COMMAND_REFERENCE.md)** - Common commands

---

**[⬅ Back to Guides](README.md)**