# System Architecture Overview

High-level architecture of ResearchAssistantGPT.

---

## 🎯 Architecture Goals

1. **Modularity**: Independent services that can be developed and deployed separately
2. **Scalability**: Ability to scale components independently
3. **Privacy**: Run entirely locally without external API calls
4. **Reliability**: Fault isolation and graceful degradation
5. **Performance**: Optimized for fast query responses

---

## 🏗️ Microservices Architecture

### Service Diagram
```
┌────────────────────────────────────────────────────────────────┐
│                         External Layer                         │
│  ┌────────────┐                              ┌──────────────┐  │
│  │    User    │                              │   n8n UI     │  │
│  │  (Browser) │                              │  (Workflow)  │  │
│  └─────┬──────┘                              └──────┬───────┘  │
└────────┼────────────────────────────────────────────┼──────────┘
         │                                            │
         └────────────────────┬───────────────────────┘
                              │
┌─────────────────────────────┼──────────────────────────────────┐
│                    Application Layer                           │
│                              │                                 │
│                    ┌─────────▼──────────┐                      │
│                    │   API Gateway      │                      │
│                    │   (FastAPI:8000)   │                      │
│                    └─────────┬──────────┘                      │
│                              │                                 │
│          ┌───────────────────┼──────────────────┐              │
│          │                   │                  │              │
│    ┌─────▼──────┐   ┌───────▼────────┐  ┌─────▼────────┐       │
│    │    RAG     │   │  CrewAI Service│  │    Ollama    │       │
│    │  Pipeline  │   │    (:8100)     │  │   (:11434)   │       │
│    └─────┬──────┘   └───────┬────────┘  └──────────────┘       │
└──────────┼──────────────────┼──────────────────────────────────┘
           │                  │
┌──────────┼──────────────────┼──────────────────────────────────┐
│                         Data Layer                             │
│    ┌─────▼──────────────┐   │                                  │
│    │     Weaviate       │   │                                  │
│    │  Vector Database   │   │                                  │
│    │     (:8080)        │   │                                  │
│    └────────────────────┘   │                                  │
│                             │                                  │
│    ┌────────────────────────▼───┐                              │
│    │      PostgreSQL            │                              │
│    │  (n8n + TruLens DB)        │                              │
│    │        (:5432)             │                              │
│    └────────────────────────────┘                              │
└────────────────────────────────────────────────────────────────┘
```

---

## 📦 Service Descriptions

### API Gateway (Port 8000)
**Technology**: FastAPI + Uvicorn  
**Responsibility**: Single entry point for all external requests

**Functions**:
- Route requests to appropriate services
- Input validation (Pydantic schemas)
- Error handling and response formatting
- Health checks and monitoring
- Proxy to CrewAI service

**Endpoints**:
- `/health`, `/ready` - Health checks
- `/rag/*` - RAG operations (ingest, query, stats)
- `/research/*` - Complete research workflow
- `/crewai/*` - Multi-agent operations (proxy)
- `/ollama/*` - LLM operations (proxy)

---

### CrewAI Service (Port 8100)
**Technology**: CrewAI 1.3.0 + LangChain + FastAPI  
**Responsibility**: Multi-agent orchestration

**Functions**:
- Execute multi-agent workflows
- Coordinate Writer → Reviewer → FactChecker
- Manage agent state and communication
- Context retrieval from Weaviate
- LLM interaction via Ollama

**Agents**:
1. **Writer**: Draft summary from context
2. **Reviewer**: Improve clarity and grammar
3. **FactChecker**: Validate claims and citations

---

### Weaviate (Port 8080)
**Technology**: Weaviate 1.23.0  
**Responsibility**: Vector database and hybrid search

**Functions**:
- Store document chunks with embeddings
- Hybrid retrieval (BM25 + vector similarity)
- Schema management (ResearchDocument class)
- Metadata filtering
- Fast nearest-neighbor search

**Schema**:
- `ResearchDocument` class
- Properties: content, source, metadata, embeddings
- Vectors: 384-dimensional (all-MiniLM-L6-v2)

---

### Ollama (Port 11434)
**Technology**: Ollama  
**Responsibility**: Local LLM inference

**Functions**:
- Run LLM models locally
- Generate text completions
- Support multiple models
- GPU acceleration (optional)
- Model management

**Default Model**: qwen3:1.7b (1.7B parameters)  
**Alternatives**: qwen3:4b, qwen2.5:3b, llama3.2:3b

---

### n8n (Port 5678)
**Technology**: n8n workflow automation  
**Responsibility**: Workflow orchestration

**Functions**:
- Trigger automated workflows
- Schedule recurring tasks
- Chain API calls
- Conditional logic
- External integrations (email, webhooks)

**Use Cases**:
- Daily ArXiv digest
- Scheduled research summaries
- Email notifications
- Custom automation

---

### PostgreSQL (Port 5432)
**Technology**: PostgreSQL 15  
**Responsibility**: Persistent data storage

**Databases**:
- `research_assistant` - n8n workflow data
- `trulens` - Evaluation metrics (experimental)

---

## 🔄 Communication Patterns

### 1. Request-Response (Synchronous)

**Pattern**: Client → API → Service → Response

**Example**: Query endpoint
```
User → API Gateway → CrewAI → Ollama → CrewAI → API → User
```

**Characteristics**:
- Blocking (waits for response)
- Real-time feedback
- Direct error handling

---

### 2. Async Background Processing (Future)

**Pattern**: Client → API → Queue → Worker → Callback

**Example**: Large document ingestion
```
User → API (return job ID) → Background worker → Callback
```

**Characteristics**:
- Non-blocking
- Handles long-running tasks
- Progress tracking

---

### 3. Event-Driven (n8n)

**Pattern**: Trigger → Workflow → Actions

**Example**: Daily digest
```
Cron Trigger → n8n → API (ingest) → API (query) → Email
```

**Characteristics**:
- Decoupled
- Scheduled execution
- Complex workflows

---

## 🌐 Network Architecture

### Docker Network: `research_net`

All services run on a single Docker bridge network.

**Internal DNS**:
- Services use service names: `api`, `weaviate`, `ollama`, `crewai`
- Example: `http://api:8000` (NOT `localhost:8000`)

**Port Mapping**:
| Internal | External | Service |
|----------|----------|---------|
| 8000 | 8000 | API |
| 8100 | 8100 | CrewAI |
| 8080 | 8080 | Weaviate |
| 11434 | 11434 | Ollama |
| 5678 | 5678 | n8n |
| 5432 | 5432 | PostgreSQL |

**Security**:
- All communication within Docker network
- Only mapped ports accessible from host
- No external network calls (privacy-preserving)

---

## 💾 Data Storage

### Volume Mounts

**Named Volumes** (persistent):
- `postgres_data`: PostgreSQL database
- `weaviate_data`: Vector embeddings and schema
- `ollama_data`: LLM models
- `n8n_data`: Workflow definitions

**Bind Mounts** (development):
- `./data/raw` → `/app/data/raw`: Local documents
- `./data/arxiv` → `/app/data/arxiv`: ArXiv downloads
- `./outputs` → `/app/outputs`: Generated summaries
- `./configs` → `/app/configs`: Configuration files

---

## 🔐 Security Model

### Current (Local Deployment)

**Threat Model**: Trusted single-user environment

**Security Measures**:
- Network isolation (Docker internal network)
- No internet exposure (localhost only)
- No authentication (trusted environment)
- Input validation (Pydantic, Guardrails)
- Content safety (Guardrails)

### Future (Production Deployment)

**Threat Model**: Multi-user, internet-exposed

**Planned Security**:
- JWT authentication
- API key management
- HTTPS/TLS encryption
- Rate limiting
- RBAC (role-based access control)
- Audit logging

---

## 📊 Performance Optimization

### Caching Strategy

**Current**:
- RAG pipeline singleton (avoid re-initialization)
- Ollama model persistence (KEEP_ALIVE=30m)

**Future**:
- Redis cache for frequent queries
- Embedding cache
- Response cache

### Resource Limits

**Ollama**:
- Memory: 6GB limit
- Models: 1 loaded at a time
- Parallel requests: 1

**Configurable** via `docker/.env`

---

## 🔄 Deployment Strategies

### Local Development
- **DevContainer**: VS Code development environment
- **Hot Reload**: API service with `--reload` flag
- **Volume Mounts**: Code changes reflected immediately

### Production (Future)
- **Docker Compose**: Production compose file
- **Kubernetes**: Helm charts for K8s deployment
- **Cloud**: AWS/GCP/Azure deployment guides

---

## 📈 Scalability

### Vertical Scaling (Current)
- Increase Docker resource allocation
- Add GPU for Ollama
- More CPU/RAM per service

### Horizontal Scaling (Future)
- Load balancer for API gateway
- Multiple CrewAI workers
- Weaviate replication
- PostgreSQL read replicas

---

## 🔍 Monitoring & Observability

### Current
- Docker logs (`docker compose logs`)
- Health check endpoints
- Manual testing

### Planned
- **TruLens**: RAG quality metrics
- **Prometheus**: System metrics
- **Grafana**: Dashboards
- **Structured logging**: JSON logs

---

## 📚 Related Documents

- **[Data Flow](DATA_FLOW.md)** - Request flow diagrams
- **[Services](SERVICES.md)** - Detailed service configs
- **[Agents](AGENTS.md)** - Multi-agent system
- **[RAG Pipeline](RAG_PIPELINE.md)** - RAG implementation

---

**[⬅ Back to Architecture](README.md)**