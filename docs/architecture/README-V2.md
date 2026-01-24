# Architecture Documentation

System design and technical architecture of ResearchAssistantGPT.

---

## 📚 Architecture Guides

| Document | Description |
|----------|-------------|
| [**System Design**](SYSTEM_DESIGN.md) | High-level architecture overview |
| [**RAG Pipeline**](RAG_PIPELINE.md) | Retrieval & generation details |
| [**Agent System**](AGENTS.md) | Multi-agent workflow |
| [**Data Flow**](DATA_FLOW.md) | Request lifecycle |

---

## 🏗️ High-Level Architecture
```
┌─────────────────────────────────────────────────────────┐
│                        User Layer                        │
├─────────────────────────────────────────────────────────┤
│  cURL  │  Python Client  │  n8n Workflows  │  Swagger  │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                 │
│  ┌─────────────┬─────────────┬─────────────────────┐   │
│  │ /rag/ingest │ /rag/query  │ /health  │ /stats   │   │
│  └─────────────┴─────────────┴─────────────────────┘   │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│              CrewAI Service (Agent Orchestration)        │
│  ┌──────────┬────────────┬──────────────────────────┐  │
│  │  Writer  │  Reviewer  │  FactChecker  │ (Future) │  │
│  └──────────┴────────────┴──────────────────────────┘  │
└────┬───────────────────────────────────┬────────────────┘
     │                                   │
     ▼                                   ▼
┌─────────────────────┐         ┌──────────────────────┐
│   RAG Pipeline      │         │   Ollama (LLM)       │
│  ┌──────────────┐   │         │  ┌────────────────┐  │
│  │  Embedder    │   │         │  │  qwen2.5:3b    │  │
│  │  Retriever   │   │         │  │  (Local Model) │  │
│  │  Chunker     │   │         │  └────────────────┘  │
│  └──────────────┘   │         └──────────────────────┘
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│              Weaviate (Vector Database)                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Class: ResearchDocument                           │ │
│  │  ├─ content (text)                                 │ │
│  │  ├─ source (text)                                  │ │
│  │  ├─ chunk_index (int)                              │ │
│  │  ├─ chunk_hash (text)                              │ │
│  │  └─ vector (float[384])                            │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow

### Query Request Lifecycle
```
1. User → API: POST /rag/query
   ├─ Input validation
   ├─ Query length check (<10,000 chars)
   └─ Language validation (en, de, fr, es)

2. API → CrewAI: Forward request
   ├─ Proxy to CrewAI service
   └─ Wait for agent processing

3. CrewAI → RAG Pipeline: Retrieve context
   ├─ Generate query embedding
   ├─ Hybrid search (BM25 + vector)
   ├─ Retrieve top-k chunks
   └─ Format context string

4. CrewAI → Ollama: Multi-agent workflow
   ├─ Writer Agent: Draft summary
   │  ├─ Input: query + context
   │  ├─ Output: draft with citations
   │  └─ Time: ~10s
   │
   ├─ Reviewer Agent: Improve clarity
   │  ├─ Input: draft
   │  ├─ Output: improved draft
   │  └─ Time: ~5s
   │
   └─ FactChecker Agent: Validate claims
      ├─ Input: reviewed draft + context
      ├─ Output: fact-checked summary
      └─ Time: ~10s

5. CrewAI → API: Return final output
   └─ Include source documents

6. API → User: JSON response
   ├─ answer (with citations)
   ├─ source_documents
   └─ metadata
```

**Total time:** 25-35 seconds per query

---

## 🧩 Component Details

### 1. API Gateway (FastAPI)

**Responsibilities:**
- HTTP endpoint exposure
- Request validation
- Response formatting
- Error handling
- Health checks

**Technology:** FastAPI + Uvicorn

**Key files:**
- `src/api/main.py` - Application entrypoint
- `src/api/routers/rag.py` - RAG endpoints

---

### 2. CrewAI Service

**Responsibilities:**
- Agent orchestration
- Workflow execution
- Task delegation
- Result aggregation

**Technology:** CrewAI framework

**Agents:**
- **Writer** - Drafts summaries
- **Reviewer** - Improves clarity
- **FactChecker** - Validates claims

**Key files:**
- `src/agents/crews/research_crew.py` - Crew definition
- `src/agents/runner.py` - Execution logic
- `src/agents/tasks/` - Task definitions

---

### 3. RAG Pipeline

**Responsibilities:**
- Document ingestion
- Text chunking
- Embedding generation
- Hybrid retrieval
- Context formatting

**Technology:** Haystack 2.x

**Components:**
- **Embedder** - sentence-transformers
- **Retriever** - Weaviate client
- **Chunker** - Custom implementation

**Key files:**
- `src/rag/core/pipeline.py` - Main pipeline
- `src/rag/ingestion/engine.py` - Ingestion
- `src/rag/sources/` - Data sources

---

### 4. Weaviate

**Responsibilities:**
- Vector storage
- Semantic search
- Hybrid ranking
- Deduplication

**Technology:** Weaviate 1.23.0

**Schema:**
```python
{
  "class": "ResearchDocument",
  "vectorizer": "none",  # We provide embeddings
  "properties": [
    {"name": "content", "dataType": ["text"]},
    {"name": "source", "dataType": ["text"]},
    {"name": "chunk_index", "dataType": ["int"]},
    {"name": "chunk_hash", "dataType": ["text"]}
  ]
}
```

---

### 5. Ollama

**Responsibilities:**
- LLM inference
- Text generation
- Local model hosting

**Technology:** Ollama

**Model:** qwen2.5:3b (3.5B parameters)

**Why qwen2.5:3b?**
- Small enough to run on CPU
- Good multilingual support
- Fast inference (~2s per response)
- Open-source

---

## 🗄️ Data Architecture

### Document Storage
```
data/
├── raw/           # User uploads
│   ├── paper1.pdf
│   └── paper2.txt
│
├── arxiv/         # ArXiv downloads
│   ├── arxiv-2301.12345-transformer-architecture.pdf
│   └── arxiv-2302.67890-rag-systems.pdf
│
└── external/      # External datasets (unused)
```

### Vector Storage

**Weaviate stores:**
- Text chunks (500 chars each)
- Embeddings (384 dimensions)
- Metadata (source, chunk_index, hash)

**Persistence:**
- Docker volume: `weaviate_data`
- Survives container restarts
- Lost on `docker compose down -v`

### Outputs
```
outputs/
├── 20250124_102030_machine-learning-summary.md
├── 20250124_103045_transformer-architecture-summary.md
└── ...
```

---

## 🔐 Security Considerations

### Current State
- ❌ No authentication
- ❌ No authorization
- ❌ No rate limiting
- ⚠️ Input validation (partial)
- ✅ Content safety checks (Guardrails)

### Future Improvements
- JWT authentication
- Role-based access control
- Rate limiting (per IP, per user)
- HTTPS/TLS
- API key management

---

## 📊 Performance Characteristics

### Latency

| Operation | Average | P95 | P99 |
|-----------|---------|-----|-----|
| Ingestion (per paper) | 5-10s | 15s | 20s |
| Query (full workflow) | 25s | 35s | 45s |
| Retrieval only | 0.5s | 1s | 2s |
| Health check | <50ms | <100ms | <200ms |

### Throughput

- **Ingestion:** ~6 papers/minute
- **Queries:** ~2 queries/minute (sequential)
- **Concurrent queries:** Limited by Ollama (1 at a time)

### Resource Usage

| Service | CPU (idle) | CPU (active) | RAM |
|---------|------------|--------------|-----|
| API | <1% | 10-20% | ~200MB |
| CrewAI | <1% | 20-30% | ~300MB |
| Weaviate | 5-10% | 20-30% | ~500MB |
| Ollama | <1% | 80-100% | ~2GB |
| PostgreSQL | <1% | 5% | ~100MB |

---

## 🔮 Future Architecture

### Planned Improvements

1. **Caching Layer** (Redis)
   - Cache frequent queries
   - Reduce duplicate work
   - Target: 50% cache hit rate

2. **Async Processing** (Celery)
   - Background ingestion
   - Queue management
   - Progress tracking

3. **Horizontal Scaling**
   - Multiple API instances
   - Load balancer
   - Shared cache

4. **Monitoring Stack**
   - Prometheus (metrics)
   - Grafana (dashboards)
   - Jaeger (tracing)

---

## 📖 Further Reading

- [**System Design**](SYSTEM_DESIGN.md) - Detailed architecture
- [**RAG Pipeline**](RAG_PIPELINE.md) - Retrieval details
- [**Agent System**](AGENTS.md) - Multi-agent workflows
- [**Data Flow**](DATA_FLOW.md) - Request lifecycle

---

**[⬅ Back to Main README](../../README.md)**