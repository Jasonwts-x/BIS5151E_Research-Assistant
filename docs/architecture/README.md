# Architecture Documentation

System design and architecture decisions for ResearchAssistantGPT.

## Table of Contents

1. [System Overview](#system-overview)
2. [Service Architecture](#service-architecture)
3. [Data Flow](#data-flow)
4. [Component Details](#component-details)
5. [Design Decisions](#design-decisions)
6. [Scalability](#scalability)
7. [Security](#security)

---

## System Overview

ResearchAssistantGPT follows a **microservices architecture** with clear separation of concerns:
```
┌─────────────────────────────────────────────────────┐
│                 Presentation Layer                   │
│              (n8n Workflow Engine)                   │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              Application Layer                       │
│   ┌──────────────────┐      ┌────────────────────┐ │
│   │   API Gateway    │◄────►│  CrewAI Service    │ │
│   │   (FastAPI)      │      │  (Multi-Agent)     │ │
│   └────────┬─────────┘      └──────────┬─────────┘ │
└────────────┼────────────────────────────┼───────────┘
             │                            │
┌────────────▼────────────────────────────▼───────────┐
│              Infrastructure Layer                    │
│   ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│   │Weaviate  │  │  Ollama  │  │   PostgreSQL     ││
│   │(Vector DB│  │  (LLM)   │  │   (n8n DB)       ││
│   └──────────┘  └──────────┘  └──────────────────┘│
└──────────────────────────────────────────────────────┘
```

---

## Service Architecture

### Gateway Pattern

**API Service** acts as the single entry point:
- Routes requests to appropriate services
- Handles authentication (future)
- Provides unified error handling
- Centralizes logging and monitoring

### Service Separation

| Service | Responsibility | Why Separate? |
|---------|---------------|---------------|
| **api** | Gateway & routing | Single entry point |
| **crewai** | Multi-agent orchestration | Isolate AI logic, enable scaling |
| **ollama** | LLM inference | Resource-intensive, needs GPU |
| **weaviate** | Vector search | Specialized database |
| **n8n** | Workflow automation | External orchestration |
| **postgres** | Data persistence | Standard database |

### Inter-Service Communication
```
┌─────────┐
│   n8n   │
└────┬────┘
     │ HTTP
┌────▼────────────────────┐
│   API Gateway           │
│   Port 8000             │
└────┬────────────┬───────┘
     │            │
     │ HTTP       │ HTTP
     │            │
┌────▼────┐  ┌───▼──────┐
│   RAG   │  │  CrewAI  │
│ Service │  │  Service │
│         │  │ Port 8100│
└────┬────┘  └────┬─────┘
     │            │
     │ gRPC       │ HTTP
     │            │
┌────▼─────┐ ┌───▼──────┐
│ Weaviate │ │  Ollama  │
│ Port 8080│ │Port 11434│
└──────────┘ └──────────┘
```

**Communication Protocols**:
- **HTTP/REST**: Inter-service (api ↔ crewai)
- **gRPC**: Weaviate client library
- **Docker Network**: All services on `research_net`

---

## Data Flow

### Query Flow (End-to-End)
```
1. User Input
   ↓
2. n8n Workflow
   ↓ POST /rag/query
3. API Gateway
   ↓ Proxy
4. CrewAI Service
   ├─ 4a. RAG Pipeline
   │  ├─ Embed query (sentence-transformers)
   │  ├─ Hybrid search (Weaviate)
   │  └─ Retrieve top-k chunks
   │
   ├─ 4b. Writer Agent (Ollama)
   │  └─ Draft summary from context
   │
   ├─ 4c. Reviewer Agent (Ollama)
   │  └─ Improve clarity
   │
   └─ 4d. FactChecker Agent (Ollama)
      └─ Verify claims
   ↓
5. Return Summary
   ↓
6. n8n Post-Processing
   └─ Save to file, send email, etc.
```

### Ingestion Flow
```
1. Source Selection
   ├─ Local Files (data/raw/)
   └─ ArXiv API
   ↓
2. Document Loading
   ├─ PDF → PyPDF
   └─ TXT → TextFileToDocument
   ↓
3. Chunking
   └─ DocumentSplitter (Haystack)
       • split_by: word
       • split_length: 350
       • split_overlap: 60
   ↓
4. Embedding
   └─ SentenceTransformersDocumentEmbedder
       • model: all-MiniLM-L6-v2
       • Output: 384-dim vectors
   ↓
5. ID Generation
   └─ Content-hash (SHA-256)
       • Deterministic
       • Automatic deduplication
   ↓
6. Storage
   └─ Weaviate
       • Batch insert
       • Skip duplicates (UUID collision)
```

---

## Component Details

### 1. API Gateway (FastAPI)

**Purpose**: Unified entry point for all services

**Responsibilities**:
- Route requests to appropriate services
- Request validation (Pydantic)
- Error handling and response formatting
- (Future) Authentication & rate limiting

**Technology**:
- Framework: FastAPI
- ASGI Server: Uvicorn
- Async: httpx for service calls

**Endpoints**:
- `/health`, `/ready`, `/version`: System
- `/rag/*`: RAG operations
- `/ollama/*`: LLM management
- `/crewai/*`: Workflow execution

---

### 2. CrewAI Service

**Purpose**: Multi-agent research workflow

**Architecture**:
```
CrewRunner
  ├─ RAGPipeline (retrieval)
  ├─ ResearchCrew (orchestration)
  │  ├─ Writer Agent
  │  ├─ Reviewer Agent
  │  ├─ FactChecker Agent
  │  └─ Translator Agent (optional)
  ├─ GuardrailsWrapper (safety)
  └─ TruLensMonitor (monitoring)
```

**Agent Communication**:
- **Sequential Process**: Tasks execute in order
- **Context Passing**: Each task receives previous output
- **LLM Backend**: Ollama via LangChain

**Workflow**:
1. **Writer**: Draft summary from RAG context
2. **Reviewer**: Improve clarity and structure
3. **FactChecker**: Verify all claims against sources
4. **(Optional) Translator**: Translate to target language

---

### 3. RAG Pipeline (Haystack)

**Purpose**: Retrieve relevant context for queries

**Architecture**:
```
RAGPipeline
  ├─ WeaviateDocumentStore
  ├─ WeaviateHybridRetriever
  │  ├─ Lexical Search (BM25)
  │  └─ Vector Search (HNSW)
  └─ SentenceTransformersTextEmbedder
```

**Hybrid Retrieval**:
- **Lexical**: Keyword matching (BM25)
- **Semantic**: Vector similarity (cosine)
- **Combined**: Reciprocal Rank Fusion

**Why Hybrid?**:
- Better than pure vector search
- Handles both semantic and exact matches
- Improved recall and precision

---

### 4. Vector Database (Weaviate)

**Purpose**: Store and search document embeddings

**Schema**:
```yaml
Class: ResearchDocument
Properties:
  - content (text, searchable)
  - source (text, filterable)
  - document_id (text)
  - chunk_index (int)
  - chunk_hash (text, unique)
  - authors (text[])
  - publication_date (text)
  - arxiv_id (text)
  - abstract (text)
  - ingestion_timestamp (text)
  - schema_version (text)
Vector: 384-dim (all-MiniLM-L6-v2)
```

**Indexing**:
- **HNSW**: Hierarchical Navigable Small World
- **M**: 16 (connections per node)
- **efConstruction**: 64 (build quality)

**Performance**:
- **Insert**: ~100 docs/sec
- **Query**: <50ms for top-k=5
- **Storage**: ~1KB per chunk

---

### 5. LLM Runtime (Ollama)

**Purpose**: Local LLM inference

**Model**: qwen2.5:3b
- **Parameters**: 3 billion
- **Context**: 32K tokens
- **Speed**: ~20 tokens/sec (CPU)
- **Memory**: ~4GB RAM

**Why Ollama?**:
- Local deployment (privacy)
- Easy model management
- GPU support
- Compatible with OpenAI API

**Alternative Models**:
- `qwen3:4b`: Better quality, slower
- `tinyllama:1.1b`: Faster, lower quality
- `mistral:7b`: Best quality (requires GPU)

---

### 6. Workflow Engine (n8n)

**Purpose**: End-to-end automation

**Capabilities**:
- HTTP requests (call API)
- Scheduling (cron jobs)
- Conditionals (if-then logic)
- Data transformation
- Integrations (email, Slack, etc.)

**Example Workflow**:
```
1. Schedule Trigger (daily 9am)
   ↓
2. HTTP Request: POST /rag/ingest/arxiv
   ↓
3. Condition: success?
   ├─ Yes: Continue
   └─ No: Send alert email
   ↓
4. HTTP Request: POST /rag/query
   ↓
5. Save to File
   ↓
6. Send Email with summary
```

---

## Design Decisions

### 1. Why Microservices?

**Pros**:
- Independent scaling (scale Ollama separately)
- Technology flexibility (different languages per service)
- Fault isolation (CrewAI failure doesn't crash API)
- Development velocity (parallel work)

**Cons**:
- More complex deployment
- Network overhead
- Distributed debugging

**Decision**: Microservices **because**:
- GPU resources needed only for Ollama
- CrewAI logic separate from API routing
- Future: Scale Ollama horizontally

---

### 2. Why Haystack over LangChain?

**Comparison**:

| Feature | Haystack | LangChain |
|---------|----------|-----------|
| RAG Pipeline | ✅ First-class | ⚠️ Add-on |
| Type Safety | ✅ Strong | ⚠️ Weak |
| Production-Ready | ✅ Yes | ⚠️ Mixed |
| Flexibility | ⚠️ Structured | ✅ Very flexible |

**Decision**: Haystack **because**:
- Better for production RAG
- Type-safe pipeline components
- Active maintenance

---

### 3. Why Weaviate over Alternatives?

**Comparison**:

| Feature | Weaviate | Pinecone | Qdrant |
|---------|----------|----------|--------|
| Self-Hosted | ✅ Yes | ❌ Cloud only | ✅ Yes |
| Hybrid Search | ✅ Built-in | ❌ No | ✅ Yes |
| Cost | ✅ Free | 💰 Expensive | ✅ Free |
| Maturity | ✅ Production | ✅ Production | ⚠️ Growing |

**Decision**: Weaviate **because**:
- Self-hosted (privacy requirement)
- Hybrid search out-of-the-box
- Good Haystack integration

---

### 4. Why Content-Hash IDs?

**Problem**: Prevent duplicate documents during re-ingestion

**Alternatives**:
1. **Auto-increment**: Not deterministic
2. **UUID**: Random, can't detect duplicates
3. **Content-hash**: ✅ Deterministic

**Implementation**:
```python
hash_input = f"{source}::{content}::{chunk_index}"
chunk_id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
```

**Benefits**:
- Same content → same ID
- Automatic deduplication
- Idempotent ingestion

---

## Scalability

### Current Limitations

| Component | Bottleneck | Max Throughput |
|-----------|-----------|----------------|
| Ollama (CPU) | Inference speed | ~20 tokens/sec |
| Weaviate | Single node | ~100 inserts/sec |
| API | Single process | ~50 req/sec |

### Scaling Strategies

**Horizontal Scaling**:
```yaml
# docker-compose.yml
services:
  ollama:
    deploy:
      replicas: 3  # 3x inference capacity
  
  api:
    deploy:
      replicas: 2  # Load balance requests
```

**Vertical Scaling**:
- Ollama: Add GPU (3-5x faster)
- Weaviate: More RAM (larger indexes)

**Caching**:
- Redis for query results
- TTL: 1 hour for summaries

---

## Security

### Current Status

⚠️ **Development Mode**: Minimal security

**No Authentication**: API is open
**No Rate Limiting**: Unlimited requests
**No Encryption**: HTTP (not HTTPS)

### Production Hardening

**Required Changes**:
1. **Add Authentication**:
```python
   # JWT tokens
   from fastapi.security import HTTPBearer
   security = HTTPBearer()
```

2. **Enable HTTPS**:
```yaml
   # docker-compose.yml
   services:
     api:
       environment:
         - CERT_FILE=/certs/cert.pem
         - KEY_FILE=/certs/key.pem
```

3. **Add Rate Limiting**:
```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   
   @app.get("/rag/query")
   @limiter.limit("10/minute")
   def query(...):
       ...
```

4. **Network Segmentation**:
```yaml
   networks:
     public:  # api, n8n
     private:  # weaviate, ollama, postgres
```

---

## Monitoring & Observability

### Logging

**Current**: Python logging to stdout

**Production**: Structured logging
```python
import structlog
logger = structlog.get_logger()
logger.info("query_executed", query=query, duration_ms=duration)
```

### Metrics

**Future**: Prometheus + Grafana
```python
from prometheus_client import Counter, Histogram

query_counter = Counter('queries_total', 'Total queries')
query_duration = Histogram('query_duration_seconds', 'Query duration')
```

### Tracing

**Future**: OpenTelemetry
```python
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("rag_query"):
    # ... query logic
```

---

## References

- [Haystack Documentation](https://docs.haystack.deepset.ai/)
- [Weaviate Architecture](https://weaviate.io/developers/weaviate/concepts)
- [CrewAI Documentation](https://docs.crewai.com/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/deployment/)

---

**[⬆ Back to Documentation](../README.md)**