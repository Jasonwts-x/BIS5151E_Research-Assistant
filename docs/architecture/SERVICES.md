# Docker Services Configuration

Detailed documentation for all Docker Compose services.

---

## 📋 Service Overview

| Service | Image | Purpose | Dependencies |
|---------|-------|---------|--------------|
| **postgres** | postgres:15 | n8n database | - |
| **weaviate** | semitechnologies/weaviate:latest | Vector database | - |
| **ollama** | ollama/ollama:latest | LLM runtime | - |
| **ollama-init** | ollama/ollama:latest | Model downloader | ollama |
| **n8n** | n8nio/n8n:latest | Workflow automation | postgres |
| **api** | (multi-stage build) | API gateway | weaviate, ollama |
| **crewai** | (multi-stage build) | Multi-agent service | weaviate, ollama |

---

## 🐘 PostgreSQL

### Configuration
```yaml
image: postgres:15
container_name: postgres
restart: unless-stopped
ports:
  - "5432:5432"
networks:
  - research_net
environment:
  POSTGRES_DB: research_assistant
  POSTGRES_USER: research_assistant
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
volumes:
  - postgres_data:/var/lib/postgresql/data
  - ../database/init:/docker-entrypoint-initdb.d:ro
```

### Purpose
- Store n8n workflow data
- Store TruLens evaluation metrics (experimental)

### Databases
- `research_assistant` - Main database for n8n
- `trulens` - Evaluation metrics (created by init script)

### Health Check
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U research_assistant -d research_assistant"]
  start_period: 10s
  interval: 10s
  timeout: 5s
  retries: 5
```

### Volume Mounts
- `postgres_data:/var/lib/postgresql/data` - Persistent data
- `../database/init:/docker-entrypoint-initdb.d:ro` - Initialization scripts

### Environment Variables
| Variable | Default | Purpose |
|----------|---------|---------|
| POSTGRES_DB | research_assistant | Database name |
| POSTGRES_USER | research_assistant | Database user |
| POSTGRES_PASSWORD | (required) | Database password |

---

## 🔍 Weaviate

### Configuration
```yaml
image: semitechnologies/weaviate:latest
container_name: weaviate
restart: unless-stopped
ports:
  - "8080:8080"
  - "50051:50051"
networks:
  - research_net
environment:
  QUERY_DEFAULTS_LIMIT: 25
  AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
  PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
  DEFAULT_VECTORIZER_MODULE: "none"
  ENABLE_MODULES: "text2vec-ollama, generative-ollama"
  CLUSTER_HOSTNAME: "node-1"
volumes:
  - weaviate_data:/var/lib/weaviate
```

### Purpose
- Vector database for document chunks
- Hybrid search (BM25 + vector similarity)
- Schema management

### Ports
- `8080` - HTTP API
- `50051` - gRPC API (optional)

### Health Check
```yaml
healthcheck:
  test: ["CMD", "wget", "--spider", "-q", "http://localhost:8080/v1/.well-known/ready"]
  start_period: 10s
  interval: 10s
  timeout: 5s
  retries: 10
```

### Environment Variables
| Variable | Value | Purpose |
|----------|-------|---------|
| DEFAULT_VECTORIZER_MODULE | none | We provide embeddings |
| AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED | true | No auth for local use |
| ENABLE_MODULES | text2vec-ollama, generative-ollama | Future Ollama integration |

### Volume Mounts
- `weaviate_data:/var/lib/weaviate` - Vector embeddings and schema

---

## 🦙 Ollama

### Configuration
```yaml
image: ollama/ollama:latest
container_name: ollama
restart: unless-stopped
deploy:
  resources:
    limits:
      memory: 6G
    reservations:
      memory: 4G
ports:
  - "11434:11434"
networks:
  - research_net
environment:
  OLLAMA_HOST: 0.0.0.0:11434
  OLLAMA_ORIGINS: "*"
  OLLAMA_NUM_PARALLEL: 1
  OLLAMA_MAX_LOADED_MODELS: 1
  OLLAMA_KEEP_ALIVE: "30m"
volumes:
  - ollama_data:/root/.ollama
```

### Purpose
- Run LLM models locally
- Provide text generation for agents
- Model management

### Resource Limits
- **Memory Limit**: 6GB
- **Memory Reservation**: 4GB
- Prevents OOM on host system

### Health Check
```yaml
healthcheck:
  test: ["CMD-SHELL", "ollama list || exit 1"]
  start_period: 10s
  interval: 10s
  timeout: 5s
  retries: 10
```

### Environment Variables
| Variable | Default | Purpose |
|----------|---------|---------|
| OLLAMA_HOST | 0.0.0.0:11434 | Listen address |
| OLLAMA_ORIGINS | * | CORS origins |
| OLLAMA_NUM_PARALLEL | 1 | Parallel requests |
| OLLAMA_MAX_LOADED_MODELS | 1 | Max models in memory |
| OLLAMA_KEEP_ALIVE | 30m | Keep model loaded |

### Volume Mounts
- `ollama_data:/root/.ollama` - Downloaded models

### GPU Support
See `docker-compose.nvidia.yml` for GPU configuration:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

---

## 🤖 Ollama-Init

### Configuration
```yaml
image: ollama/ollama:latest
container_name: ollama-init
entrypoint: ["/bin/sh", "-c"]
depends_on:
  ollama:
    condition: service_healthy
networks:
  - research_net
environment:
  OLLAMA_HOST: http://ollama:11434
volumes:
  - ollama_data:/root/.ollama
command: ["ollama pull qwen3:4b && ollama pull qwen3:1.7b && ollama pull llama3.2:3b"]
restart: "no"
```

### Purpose
- Download LLM models on first startup
- One-time initialization
- Exits after models are downloaded

### Downloaded Models
- `qwen3:4b` - 4B parameter model
- `qwen3:1.7b` - 1.7B parameter model (default)
- `llama3.2:3b` - Alternative 3B model

### Restart Policy
- `restart: "no"` - Only runs once, then exits

---

## 🌐 n8n

### Configuration
```yaml
image: n8nio/n8n:latest
container_name: n8n
restart: unless-stopped
depends_on:
  postgres:
    condition: service_healthy
    restart: true
ports:
  - "5678:5678"
networks:
  - research_net
environment:
  N8N_HOST: n8n
  N8N_PORT: 5678
  N8N_PROTOCOL: http
  N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY}
  GENERIC_TIMEZONE: Europe/Berlin
  WEBHOOK_URL: http://localhost:5678/
  DB_TYPE: postgresdb
  DB_POSTGRESDB_HOST: postgres
  DB_POSTGRESDB_PORT: 5432
  DB_POSTGRESDB_DATABASE: research_assistant
  DB_POSTGRESDB_USER: research_assistant
  DB_POSTGRESDB_PASSWORD: ${POSTGRES_PASSWORD}
volumes:
  - n8n_data:/home/node/.n8n
  - ./workflows:/home/node/workflows
```

### Purpose
- Workflow automation
- Scheduled tasks
- External integrations

### Health Check
```yaml
healthcheck:
  test: ["CMD-SHELL", "wget -qO- http://localhost:5678/healthz/readiness | grep -qi 'ok'"]
  start_period: 45s
  interval: 10s
  timeout: 5s
  retries: 10
```

### Environment Variables
| Variable | Value | Purpose |
|----------|---------|---------|
| N8N_ENCRYPTION_KEY | (required) | Encrypt credentials |
| DB_TYPE | postgresdb | Use PostgreSQL |
| DB_POSTGRESDB_HOST | postgres | Database host |
| WEBHOOK_URL | http://localhost:5678/ | Webhook base URL |

### Volume Mounts
- `n8n_data:/home/node/.n8n` - Workflow data
- `./workflows:/home/node/workflows` - Example workflows

---

## 🚀 API Gateway

### Configuration
```yaml
build:
  context: ..
  dockerfile: .devcontainer/Dockerfile
  target: api
container_name: api
working_dir: /workspaces/BIS5151E_Research-Assistant
command: uvicorn src.api.server:app --host 0.0.0.0 --port 8000
restart: unless-stopped
depends_on:
  weaviate:
    condition: service_healthy
  ollama:
    condition: service_healthy
ports:
  - "8000:8000"
networks:
  - research_net
environment:
  WEAVIATE_URL: http://weaviate:8080
  OLLAMA_HOST: http://ollama:11434
  CREWAI_URL: http://crewai:8100
volumes:
  - ../data:/workspaces/BIS5151E_Research-Assistant/data
  - ../outputs:/workspaces/BIS5151E_Research-Assistant/outputs
  - ../configs:/workspaces/BIS5151E_Research-Assistant/configs
```

### Purpose
- Single entry point for API requests
- Request routing
- Input validation
- Error handling

### Build Configuration
- **Context**: Repository root
- **Dockerfile**: `.devcontainer/Dockerfile`
- **Target**: `api` (multi-stage build)

### Health Check
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  start_period: 20s
  interval: 10s
  timeout: 5s
  retries: 10
```

### Environment Variables
| Variable | Value | Purpose |
|----------|---------|---------|
| WEAVIATE_URL | http://weaviate:8080 | Weaviate connection |
| OLLAMA_HOST | http://ollama:11434 | Ollama connection |
| CREWAI_URL | http://crewai:8100 | CrewAI connection |

### Volume Mounts
- `../data:/workspaces/.../data` - Document storage
- `../outputs:/workspaces/.../outputs` - Generated summaries
- `../configs:/workspaces/.../configs` - Configuration files

---

## 🤝 CrewAI Service

### Configuration
```yaml
build:
  context: ..
  dockerfile: .devcontainer/Dockerfile
  target: crewai
container_name: crewai
working_dir: /workspaces/BIS5151E_Research-Assistant
command: uvicorn src.agents.api.server:app --host 0.0.0.0 --port 8100
restart: unless-stopped
depends_on:
  weaviate:
    condition: service_healthy
  ollama:
    condition: service_healthy
ports:
  - "8100:8100"
networks:
  - research_net
environment:
  WEAVIATE_URL: http://weaviate:8080
  OLLAMA_HOST: http://ollama:11434
volumes:
  - ../data:/workspaces/BIS5151E_Research-Assistant/data
  - ../configs:/workspaces/BIS5151E_Research-Assistant/configs
```

### Purpose
- Multi-agent orchestration
- Execute research workflows
- Agent collaboration

### Build Configuration
- **Context**: Repository root
- **Dockerfile**: `.devcontainer/Dockerfile`
- **Target**: `crewai` (multi-stage build)

### Health Check
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
  start_period: 20s
  interval: 10s
  timeout: 5s
  retries: 10
```

### Environment Variables
| Variable | Value | Purpose |
|----------|---------|---------|
| WEAVIATE_URL | http://weaviate:8080 | Weaviate connection |
| OLLAMA_HOST | http://ollama:11434 | Ollama connection |

---

## 🌐 Network Configuration

### Docker Network
```yaml
networks:
  research_net:
    driver: bridge
```

**All services communicate via `research_net` bridge network.**

### DNS Resolution
Services use Docker DNS:
- `api` → resolves to API container
- `weaviate` → resolves to Weaviate container
- `ollama` → resolves to Ollama container
- `crewai` → resolves to CrewAI container
- `postgres` → resolves to PostgreSQL container

**Important**: Always use service names, not `localhost`!

---

## 💾 Volume Configuration

### Named Volumes
```yaml
volumes:
  postgres_data:
  weaviate_data:
  ollama_data:
  n8n_data:
```

**Persistence**: Data survives container restarts and rebuilds.

**Location**: Docker managed (`/var/lib/docker/volumes/`)

**Backup**: Use Docker volume backup commands

---

## 🔄 Service Dependencies

### Dependency Graph
```
postgres (no dependencies)
    ↓
n8n (depends on postgres)

weaviate (no dependencies)

ollama (no dependencies)
    ↓
ollama-init (depends on ollama)

weaviate + ollama
    ↓
api (depends on weaviate, ollama)
    ↓
crewai (depends on weaviate, ollama)
```

### Startup Order
1. postgres, weaviate, ollama start in parallel
2. Wait for health checks
3. n8n starts (after postgres healthy)
4. ollama-init starts (after ollama healthy)
5. api starts (after weaviate + ollama healthy)
6. crewai starts (after weaviate + ollama healthy)

---

## 📊 Resource Allocation

### Default Limits

| Service | CPU | Memory | Disk |
|---------|-----|--------|------|
| postgres | Unlimited | Unlimited | 1-5GB |
| weaviate | Unlimited | Unlimited | 5-20GB |
| ollama | Unlimited | 6GB limit | 10-20GB |
| n8n | Unlimited | Unlimited | 100MB |
| api | Unlimited | Unlimited | Minimal |
| crewai | Unlimited | Unlimited | Minimal |

### Customization

Edit `docker-compose.yml` to add limits:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

---

## 🔐 Security Configuration

### Current (Local)
- No authentication between services
- No encryption (plain HTTP)
- Anonymous Weaviate access
- Trusted network assumption

### Production (Future)
- Service-to-service authentication
- HTTPS with TLS certificates
- API key management
- Network policies

---

## 📚 Related Documentation

- **[Architecture Overview](OVERVIEW.md)** - High-level design
- **[Data Flow](DATA_FLOW.md)** - Request flow
- **[Setup Guide](../setup/INSTALLATION.md)** - Installation

---

**[⬅ Back to Architecture](README.md)**