# System Architecture

Complete technical architecture documentation for ResearchAssistantGPT.

---

## 📚 Architecture Documentation

| Document | Description |
|----------|-------------|
| **[OVERVIEW.md](OVERVIEW.md)** | High-level system architecture |
| **[DATA_FLOW.md](DATA_FLOW.md)** | Request flow and data pipelines |
| **[SERVICES.md](SERVICES.md)** | Docker services and interactions |
| **[AGENTS.md](AGENTS.md)** | Multi-agent system (CrewAI) |
| **[RAG_PIPELINE.md](RAG_PIPELINE.md)** | RAG implementation details |
| **[DATABASE.md](DATABASE.md)** | Database schemas (Weaviate, PostgreSQL) |

---

## 🏗️ Quick Overview

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                         User / n8n                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (8000)                       │
│              FastAPI + Modular Routers                      │
└────┬──────────────────────────┬──────────────┬──────────────┘
     │                          │              │
     ▼                          ▼              ▼
┌────────────┐      ┌────────────────────┐  ┌──────────────┐
│  Weaviate  │      │  CrewAI (8100)     │  │ Ollama(11434)│
│  (8080)    │◄─────│  Multi-Agent       │◄─┤ LLM Runtime  │
│  Vector DB │      │  Writer/Reviewer   │  │ qwen3:1.7b   │
└────────────┘      │  FactChecker       │  └──────────────┘
                    └────────────────────┘
```

### Core Services

| Service | Port | Purpose | Technology |
|---------|------|---------|------------|
| **API Gateway** | 8000 | REST API, request routing | FastAPI |
| **CrewAI** | 8100 | Multi-agent orchestration | CrewAI 1.3.0 |
| **Weaviate** | 8080 | Vector database, hybrid search | Weaviate 1.23.0 |
| **Ollama** | 11434 | LLM inference | Ollama + qwen3:1.7b |
| **n8n** | 5678 | Workflow automation | n8n |
| **PostgreSQL** | 5432 | n8n persistence | PostgreSQL 15 |

---

## 📖 Detailed Documentation

### [OVERVIEW.md](OVERVIEW.md)
Complete system architecture overview:
- Microservices design
- Service responsibilities
- Communication patterns
- Network topology
- Deployment architecture

### [DATA_FLOW.md](DATA_FLOW.md)
How data flows through the system:
- Ingestion pipeline (ArXiv → Weaviate)
- Query workflow (User → API → CrewAI → Ollama)
- Multi-agent collaboration
- Response generation
- Network flow diagrams

### [SERVICES.md](SERVICES.md)
Docker service configurations:
- Service dependencies
- Health checks
- Resource limits
- Environment variables
- Volume mounts
- Network configuration

### [AGENTS.md](AGENTS.md)
Multi-agent system architecture:
- Writer agent (draft generation)
- Reviewer agent (quality improvement)
- FactChecker agent (citation validation)
- Agent collaboration patterns
- Task definitions
- Crew composition

### [RAG_PIPELINE.md](RAG_PIPELINE.md)
RAG implementation details:
- Document processing
- Chunking strategy (350 chars)
- Embedding generation
- Hybrid retrieval (BM25 + vector)
- Context assembly
- Pipeline optimization

### [DATABASE.md](DATABASE.md)
Database schemas and design:
- Weaviate schema (ResearchDocument)
- PostgreSQL schema (n8n, TruLens)
- Data models
- Indexing strategy
- Query patterns

---

## 🎯 Architecture Principles

### 1. Microservices Design
- **Separation of Concerns**: Each service has a single responsibility
- **Independent Scaling**: Scale services independently
- **Fault Isolation**: Service failures don't cascade
- **Technology Freedom**: Use best tool for each job

### 2. API Gateway Pattern
- **Single Entry Point**: API gateway routes all requests
- **Service Discovery**: Internal service-to-service communication
- **Load Balancing**: Distribute load across instances (future)
- **Authentication**: Centralized auth (future)

### 3. Event-Driven Architecture
- **Asynchronous Processing**: n8n triggers workflows
- **Decoupled Services**: Services communicate via API calls
- **Workflow Orchestration**: n8n manages complex workflows

### 4. Data Locality
- **Embedded Models**: LLMs run locally (Ollama)
- **Local Vector DB**: Weaviate on same network
- **No External Calls**: Privacy-preserving design

---

## 🔍 Key Design Decisions

### Why Microservices?
**Decision**: Separate API, CrewAI, and Ollama into different services  
**Rationale**:
- Independent scaling (scale agents without scaling LLM)
- Better resource management
- Easier development and testing
- Service isolation

### Why CrewAI?
**Decision**: Use CrewAI for multi-agent orchestration  
**Rationale**:
- Built-in agent collaboration
- Task-based workflow
- LangChain integration
- Active development

### Why Weaviate?
**Decision**: Use Weaviate for vector database  
**Rationale**:
- Hybrid search (BM25 + vector)
- Fast retrieval
- Scalable
- Good Python client

### Why qwen3:1.7b?
**Decision**: Default to qwen3:1.7b model  
**Rationale**:
- Fast inference (< 10s on CPU)
- Good quality for size
- Multilingual support
- Low resource usage

---

## 📊 Performance Characteristics

### Latency Breakdown

**Full research query** (~28 seconds):
- API validation: 10ms
- RAG retrieval: 500ms
- Writer agent: 10s
- Reviewer agent: 5s
- FactChecker agent: 10s
- Response formatting: 20ms

**Ingestion** (per paper):
- PDF download: 5s
- Text extraction: 1s
- Chunking: 100ms
- Embedding: 2s
- Weaviate write: 500ms

### Resource Usage

**Minimum**:
- CPU: 4 cores
- RAM: 16GB
- Disk: 20GB

**Recommended**:
- CPU: 8 cores
- RAM: 32GB
- Disk: 50GB SSD
- GPU: NVIDIA 8GB+ VRAM

---

## 🔄 Scaling Strategy

### Horizontal Scaling (Future)

**Stateless Services** (can scale easily):
- API Gateway (multiple instances behind load balancer)
- CrewAI Service (worker pool)

**Stateful Services** (require coordination):
- Weaviate (replication)
- PostgreSQL (read replicas)
- Ollama (model sharding)

### Vertical Scaling (Current)

**Increase resources per service**:
- More CPU cores for API/CrewAI
- More RAM for Ollama
- GPU for Ollama
- SSD for Weaviate

---

## 🔐 Security Considerations

**Current** (local deployment):
- No authentication (trusted network)
- No encryption (localhost only)
- No authorization (single user)

**Future** (production):
- JWT authentication
- HTTPS/TLS encryption
- Role-based access control
- API key management
- Rate limiting

---

## 📚 Related Documentation

- **[Setup Guide](../setup/README.md)** - Installation instructions
- **[API Reference](../api/README.md)** - Endpoint documentation
- **[Examples](../examples/README.md)** - Integration examples
- **[Evaluation](../evaluation/README.md)** - Quality metrics

---

**[⬅ Back to Documentation](../README.md)**