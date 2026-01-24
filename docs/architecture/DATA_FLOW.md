# Data Flow Architecture

End-to-end request flow through the system.

---

## Request Lifecycle

### Complete Query Flow
```
┌──────────────────────────────────────────────────────────────┐
│ 1. User Request                                               │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
        POST /rag/query {"query": "What is AI?", "language": "en"}
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. API Gateway (FastAPI)                                      │
│    ┌────────────────────────────────────────────────┐        │
│    │ • Validate request                              │        │
│    │ • Check query length (<10,000 chars)           │        │
│    │ • Validate language (en, de, fr, es)           │        │
│    │ • Log request                                   │        │
│    └────────────────────────────────────────────────┘        │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
                   Proxy to CrewAI service
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. CrewAI Service                                             │
│    ┌────────────────────────────────────────────────┐        │
│    │ Initialize CrewRunner                           │        │
│    │   ├─ Load LLM connection                        │        │
│    │   ├─ Initialize RAG pipeline                    │        │
│    │   └─ Setup guardrails (optional)                │        │
│    └────────────────────────────────────────────────┘        │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. RAG Pipeline - Retrieval                                   │
│    ┌────────────────────────────────────────────────┐        │
│    │ Step 1: Generate query embedding                │        │
│    │   model.encode("What is AI?")                   │        │
│    │   → [0.123, -0.456, ..., 0.789] (384-dim)      │        │
│    │   Time: ~20ms                                   │        │
│    └────────────────────────────────────────────────┘        │
│                            ↓                                  │
│    ┌────────────────────────────────────────────────┐        │
│    │ Step 2: Hybrid search in Weaviate              │        │
│    │   • BM25 keyword search: "AI"                   │        │
│    │   • Vector similarity search: cosine(query_vec, doc_vecs)│
│    │   • Combine results (alpha=0.75)                │        │
│    │   • Retrieve top-5 chunks                       │        │
│    │   Time: ~200-500ms                              │        │
│    └────────────────────────────────────────────────┘        │
│                            ↓                                  │
│    ┌────────────────────────────────────────────────┐        │
│    │ Step 3: Format context                          │        │
│    │   context = "\n\n".join([                       │        │
│    │       f"[{i}] {doc.content}"                    │        │
│    │       for i, doc in enumerate(docs, 1)          │        │
│    │   ])                                            │        │
│    │   Time: ~10ms                                   │        │
│    └────────────────────────────────────────────────┘        │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
              Context: 5 documents, ~2500 chars
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. Multi-Agent Workflow                                       │
│                                                               │
│    ┌─────────────────────────────────────────────┐           │
│    │ Agent 1: Writer                              │           │
│    │   Input: query + context                     │           │
│    │   Prompt: "Write a summary on '{query}'...   │           │
│    │            Use ONLY this context: {context}"  │           │
│    │   LLM Call → Ollama (qwen2.5:3b)             │           │
│    │   Output: Draft summary with [1][2][3]       │           │
│    │   Time: ~10s                                  │           │
│    └─────────────────────────────────────────────┘           │
│                            ↓                                  │
│    ┌─────────────────────────────────────────────┐           │
│    │ Agent 2: Reviewer                            │           │
│    │   Input: draft from Writer                   │           │
│    │   Prompt: "Improve this draft's clarity..."  │           │
│    │   LLM Call → Ollama                          │           │
│    │   Output: Improved draft                     │           │
│    │   Time: ~5s                                   │           │
│    └─────────────────────────────────────────────┘           │
│                            ↓                                  │
│    ┌─────────────────────────────────────────────┐           │
│    │ Agent 3: FactChecker                         │           │
│    │   Input: improved draft + context            │           │
│    │   Prompt: "Verify all claims against context"│           │
│    │   LLM Call → Ollama                          │           │
│    │   Output: Fact-checked final summary         │           │
│    │   Time: ~10s                                  │           │
│    └─────────────────────────────────────────────┘           │
│                                                               │
│    Total agent time: ~25s                                     │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
                    Final summary generated
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. Response Preparation                                       │
│    ┌────────────────────────────────────────────────┐        │
│    │ • Save summary to outputs/                      │        │
│    │ • Format JSON response                          │        │
│    │ • Include source documents                      │        │
│    │ • Add metadata                                  │        │
│    └────────────────────────────────────────────────┘        │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 7. API Response                                               │
│    {                                                          │
│      "query": "What is AI?",                                  │
│      "answer": "Artificial intelligence is...[1][2]",         │
│      "source_documents": [...],                               │
│      "language": "en"                                         │
│    }                                                          │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
                      User receives response
                Total time: ~26-32 seconds
```

---

## Ingestion Flow

### ArXiv Ingestion
```
User → POST /rag/ingest/arxiv {"query": "transformers", "max_results": 3}
  ↓
API validates request
  ↓
┌─────────────────────────────────────────┐
│ ArXiv Source                             │
│  1. Search ArXiv API                     │
│     query="transformers", max=3          │
│     → Returns 3 paper metadata           │
│     Time: ~2s                            │
│                                          │
│  2. Download PDFs                        │
│     For each paper:                      │
│       - Download PDF                     │
│       - Save to data/arxiv/              │
│     Time: ~15s (3 papers)                │
│                                          │
│  3. Extract text                         │
│     For each PDF:                        │
│       - Read pages                       │
│       - Extract text                     │
│       - Clean formatting                 │
│     Time: ~3s (3 papers)                 │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Document Processor                       │
│  4. Chunk documents                      │
│     For each document:                   │
│       - Split into 500-char chunks       │
│       - Apply 50-char overlap            │
│       - Generate chunk IDs (hash)        │
│     Result: ~150 chunks (3 papers)       │
│     Time: ~100ms                         │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Embedding Generator                      │
│  5. Generate embeddings                  │
│     Batch process chunks:                │
│       - model.encode(chunks, batch=32)   │
│       - 150 chunks → 150 vectors         │
│     Time: ~3s                            │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Weaviate Storage                         │
│  6. Write to database                    │
│     For each chunk:                      │
│       - Check if exists (by hash)        │
│       - If new: write to Weaviate        │
│       - If duplicate: skip               │
│     Time: ~2s                            │
└─────────────────┬───────────────────────┘
                  ↓
Response: {
  "documents_loaded": 3,
  "chunks_ingested": 150,
  "chunks_skipped": 0
}
Total time: ~25-30s
```

---

## Data Persistence

### Storage Locations
```
Docker Volumes (persistent):
├── postgres_data
│   └── n8n workflow state
├── weaviate_data
│   └── Vector embeddings + metadata
├── ollama_data
│   └── LLM models
└── n8n_data
    └── Workflow configurations

Bind Mounts (host filesystem):
├── data/raw/
│   └── User-uploaded PDFs
├── data/arxiv/
│   └── Downloaded ArXiv papers
└── outputs/
    └── Generated summaries
```

### Data Flow Diagram
```
┌──────────────┐
│ User uploads │
│   paper.pdf  │
└──────┬───────┘
       │
       ↓ (copy)
┌──────────────────┐
│  data/raw/       │
│  paper.pdf       │
└──────┬───────────┘
       │
       ↓ (ingest)
┌──────────────────────────────────┐
│  Weaviate                         │
│  ┌────────────────────────────┐  │
│  │ Chunk 1: "Introduction..." │  │
│  │ Vector: [0.1, 0.2, ...]    │  │
│  ├────────────────────────────┤  │
│  │ Chunk 2: "Methods..."      │  │
│  │ Vector: [0.3, 0.4, ...]    │  │
│  └────────────────────────────┘  │
└──────┬───────────────────────────┘
       │
       ↓ (query)
┌──────────────────┐
│  Ollama LLM      │
│  generates       │
│  summary         │
└──────┬───────────┘
       │
       ↓ (save)
┌──────────────────────────────────┐
│  outputs/                         │
│  20250124_summary.md              │
└───────────────────────────────────┘
```

---

## Network Flow

### Internal Docker Network
```
┌─────────────────────────────────────────────────────────┐
│ Docker Network: research_net                            │
│                                                         │
│  ┌──────────┐      ┌───────────┐      ┌────────────┐  │
│  │   n8n    │─────>│    API    │─────>│  CrewAI    │  │
│  │  :5678   │      │   :8000   │      │   :8001    │  │
│  └──────────┘      └─────┬─────┘      └──────┬─────┘  │
│                          │                    │         │
│                          ↓                    ↓         │
│                    ┌──────────┐         ┌──────────┐   │
│                    │ Weaviate │         │  Ollama  │   │
│                    │  :8080   │         │  :11434  │   │
│                    └──────────┘         └──────────┘   │
│                                                         │
│  ┌──────────┐                                          │
│  │PostgreSQL│                                          │
│  │  :5432   │                                          │
│  └──────────┘                                          │
└─────────────────────────────────────────────────────────┘
         ↑
         │ Port mapping to host
         ↓
┌─────────────────────┐
│  Host (localhost)   │
│  - 5678 → n8n       │
│  - 8000 → API       │
│  - 8080 → Weaviate  │
│  - 11434 → Ollama   │
└─────────────────────┘
```

**Important:** Services use **service names** for internal communication:
```python
# ✅ Correct (in containers)
WEAVIATE_URL = "http://weaviate:8080"
OLLAMA_URL = "http://ollama:11434"

# ❌ Wrong (won't work in containers)
WEAVIATE_URL = "http://localhost:8080"
```

---

## Error Propagation

### Error Handling Chain
```
User Request
     ↓
API validates
     ├─ Invalid input → 400 Bad Request (immediate)
     ├─ Service down → 503 Service Unavailable
     └─ Valid → Continue
     ↓
CrewAI processes
     ├─ LLM timeout → Retry (3x) → 500 if fails
     ├─ Context empty → Return "insufficient context"
     └─ Success → Continue
     ↓
RAG retrieves
     ├─ Weaviate down → 503 Service Unavailable
     ├─ No results → Empty context (handled by agents)
     └─ Success → Continue
     ↓
Response sent
```

---

## Performance Metrics

### Latency Breakdown

**Query endpoint:**
```
Total: ~26-32 seconds
├─ Validation:        10ms
├─ RAG retrieval:     500ms
├─ Writer agent:      10s
├─ Reviewer agent:    5s
├─ FactChecker:       10s
└─ Response format:   20ms
```

**Ingestion endpoint:**
```
Total: ~25-30 seconds (3 papers)
├─ ArXiv search:      2s
├─ PDF download:      15s
├─ Text extraction:   3s
├─ Chunking:          100ms
├─ Embedding:         3s
└─ Weaviate write:    2s
```

### Bottlenecks

1. **Ollama LLM calls** (~25s total)
   - Sequential execution
   - CPU-bound
   - Mitigation: GPU acceleration

2. **PDF downloads** (~15s for 3 papers)
   - Network I/O
   - ArXiv rate limits
   - Mitigation: Parallel downloads

3. **Weaviate search** (~500ms)
   - Scales with index size
   - Mitigation: Optimize queries, add caching

---

**[⬅ Back to Architecture](README.md)** | **[⬆ Back to Main README](../../README.md)**