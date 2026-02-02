# Data Flow Architecture

Complete data flow diagrams and request lifecycle documentation.

---

## 📊 Complete System Data Flow
```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Layer                                  │
│  ┌────────────┐              ┌──────────────┐                       │
│  │   User     │              │   n8n UI     │                       │
│  │  Browser   │              │  Workflows   │                       │
│  └──────┬─────┘              └──────┬───────┘                       │
└─────────┼────────────────────────────┼──────────────────────────────┘
          │                            │
          │ HTTP POST /research/query  │ HTTP POST /rag/ingest/arxiv
          │                            │
          ▼                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    API Gateway (Port 8000)                          │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   Validate   │→ │    Route     │→ │   Respond    │               │
│  │    Input     │  │   Request    │  │   Format     │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└────────┬──────────────────────┬──────────────────────┬──────────────┘
         │                      │                      │
         │ 1. Ingest            │ 2. Query             │ 3. Proxy
         ▼                      ▼                      ▼
┌─────────────────┐   ┌──────────────────┐   ┌─────────────────┐
│  RAG Pipeline   │   │  CrewAI Service  │   │ Ollama Service  │
│  (Ingestion)    │   │   (Port 8100)    │   │ (Port 11434)    │
└────────┬────────┘   └────────┬─────────┘   └─────────────────┘
         │                     │
         │ Store chunks        │ Retrieve context
         ▼                     ▼
┌──────────────────────────────────────────┐
│       Weaviate Vector Database           │
│           (Port 8080)                    │
│  ┌────────────────────────────────────┐  │
│  │  ResearchDocument Collection       │  │
│  │  - Chunks                          │  │
│  │  - Embeddings (384-dim)            │  │
│  │  - Metadata                        │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

## 🔄 Ingestion Flow (ArXiv)

### Step-by-Step Flow
```
1. User/n8n
   POST /rag/ingest/arxiv
   Body: {"query": "machine learning", "max_results": 3}
   │
   ▼
2. API Gateway
   - Validate request (Pydantic)
   - Call RAG pipeline
   │
   ▼
3. ArXiv Source Loader
   - Search ArXiv API
   - Download PDFs to data/arxiv/
   - Extract text with PyPDF
   │
   ▼
4. Document Processor
   - Chunk text (350 chars, 50 overlap)
   - Generate chunk metadata
   - Create chunk IDs (SHA-256 hash)
   │
   ▼
5. Embedder
   - Generate embeddings (all-MiniLM-L6-v2)
   - 384-dimensional vectors
   - Batch processing (32 chunks/batch)
   │
   ▼
6. Weaviate
   - Create ResearchDocument objects
   - Store chunks + embeddings
   - Index for search
   │
   ▼
7. API Response
   {
     "source": "arxiv",
     "documents_loaded": 3,
     "chunks_created": 142,
     "chunks_ingested": 142,
     "success": true
   }
```

### Timing Breakdown (3 papers)

| Step | Time | Percentage |
|------|------|------------|
| ArXiv search | 2s | 7% |
| PDF download | 15s | 50% |
| Text extraction | 3s | 10% |
| Chunking | 100ms | <1% |
| Embedding | 6s | 20% |
| Weaviate write | 3s | 10% |
| **Total** | **~30s** | **100%** |

---

## 🔍 Query Flow (Research Workflow)

### Complete Research Query
```
1. User/n8n
   POST /research/query
   Body: {"query": "Explain transformers", "language": "en"}
   │
   ▼
2. API Gateway
   - Validate input (Guardrails)
   - Check query length (<10k chars)
   - Sanitize input
   │
   ▼
3. Proxy to CrewAI
   POST http://crewai:8100/run
   │
   ▼
4. CrewAI Service
   ┌─────────────────────────────────────────┐
   │ Step 4a: Context Retrieval              │
   │ - Embed query (384-dim)                 │
   │ - Hybrid search Weaviate                │
   │ - Top-5 chunks returned                 │
   └─────────────────────────────────────────┘
   │
   ▼
   ┌─────────────────────────────────────────┐
   │ Step 4b: Writer Agent                   │
   │ - Input: Query + Context                │
   │ - LLM: Ollama (qwen3:1.7b)              │
   │ - Output: Draft summary (~300 words)    │
   │ - Time: ~10s                            │
   └─────────────────────────────────────────┘
   │
   ▼
   ┌─────────────────────────────────────────┐
   │ Step 4c: Reviewer Agent                 │
   │ - Input: Draft                          │
   │ - Task: Improve clarity, fix grammar    │
   │ - LLM: Ollama (qwen3:1.7b)              │
   │ - Output: Reviewed summary              │
   │ - Time: ~5s                             │
   └─────────────────────────────────────────┘
   │
   ▼
   ┌─────────────────────────────────────────┐
   │ Step 4d: FactChecker Agent              │
   │ - Input: Reviewed summary + Context     │
   │ - Task: Validate claims, check citations│
   │ - LLM: Ollama (qwen3:1.7b)              │
   │ - Output: Final summary                 │
   │ - Time: ~10s                            │
   └─────────────────────────────────────────┘
   │
   ▼
5. API Gateway
   - Validate output (Guardrails)
   - Check citations, length, safety
   │
   ▼
6. Response to User
   {
     "query": "Explain transformers",
     "answer": "Transformers are...",
     "sources": [...],
     "language": "en",
     "processing_time": 28.4
   }
```

### Timing Breakdown (Single Query)

| Step | Time | Percentage |
|------|------|------------|
| Input validation | 10ms | <1% |
| Context retrieval | 500ms | 2% |
| Writer agent | 10s | 36% |
| Reviewer agent | 5s | 18% |
| FactChecker agent | 10s | 36% |
| Output validation | 20ms | <1% |
| Response formatting | 10ms | <1% |
| **Total** | **~28s** | **100%** |

---

## 🔄 RAG Retrieval Flow (Detailed)
```
Query: "What are neural networks?"
│
▼
┌─────────────────────────────────────────┐
│ 1. Embedder                             │
│ - Model: all-MiniLM-L6-v2               │
│ - Input: query string                   │
│ - Output: 384-dim vector                │
│ - Time: ~100ms                          │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ 2. Hybrid Retriever                     │
│                                         │
│ BM25 Search (Lexical):                  │
│ - Keyword matching                      │
│ - "neural", "networks"                  │
│ - BM25 scores: [0.8, 0.7, 0.6, ...]     │
│                                         │
│ Vector Search (Semantic):               │
│ - Cosine similarity                     │
│ - Find similar meanings                 │
│ - Vector scores: [0.9, 0.85, 0.8, ...]  │
│                                         │
│ Combined Score:                         │
│ score = 0.5*BM25 + 0.5*Vector           │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ 3. Weaviate Query                       │
│ GraphQL:                                │
│ {                                       │
│   Get {                                 │
│     ResearchDocument(                   │
│       hybrid: {                         │
│         query: "neural networks"        │
│         vector: [0.1, 0.3, ...]         │
│         alpha: 0.5                      │
│       }                                 │
│       limit: 5                          │
│     ) {                                 │
│       content                           │
│       source                            │
│       _additional { score }             │
│     }                                   │
│   }                                     │
│ }                                       │
│ Time: ~300-500ms                        │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ 4. Results Returned                     │
│ [                                       │
│   {                                     │
│     "content": "Neural networks are...",│
│     "source": "paper1.pdf",             │
│     "score": 0.89                       │
│   },                                    │
│   {                                     │
│     "content": "A neural network...",   │
│     "source": "paper2.pdf",             │
│     "score": 0.85                       │
│   },                                    │
│   ...                                   │
│ ]                                       │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ 5. Context Assembly                     │
│ context = """                           │
│ Source: paper1.pdf                      │
│ Neural networks are...                  │
│                                         │
│ Source: paper2.pdf                      │
│ A neural network...                     │
│ """                                     │
└─────────────────────────────────────────┘
│
▼
Return to CrewAI for agent processing
```

---

## 🤖 Multi-Agent Collaboration Flow
```
Context Retrieved from Weaviate
│
▼
┌──────────────────────────────────────────────────────┐
│ Writer Agent (Role: Research Writer)                 │
│                                                      │
│ Input:                                               │
│ - Query: "Explain transformers"                      │
│ - Context: 5 relevant chunks                         │
│                                                      │
│ Task:                                                │
│ "Write a concise 300-word summary on {topic}.        │
│  Use provided context. Include citations [1], [2]."  │
│                                                      │
│ LLM Call to Ollama:                                  │
│ - Model: qwen3:1.7b                                  │
│ - Temperature: 0.3                                   │
│ - Max tokens: 500                                    │
│                                                      │
│ Output:                                              │
│ Draft: "Transformers are neural network              │
│ architectures that use self-attention [1]..."        │
│                                                      │
│ Time: ~10s                                           │
└──────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────┐
│ Reviewer Agent (Role: Content Reviewer)              │
│                                                      │
│ Input:                                               │
│ - Draft from Writer                                  │
│                                                      │
│ Task:                                                │
│ "Review and improve clarity and grammar.             │
│  Keep same meaning. Don't add new facts."            │
│                                                      │
│ LLM Call to Ollama:                                  │
│ - Model: qwen3:1.7b                                  │
│ - Temperature: 0.2 (lower for consistency)           │
│                                                      │
│ Output:                                              │
│ Reviewed: "Transformers are neural network           │
│ architectures that utilize self-attention            │
│ mechanisms [1]..."                                   │
│                                                      │
│ Time: ~5s                                            │
└──────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────┐
│ FactChecker Agent (Role: Fact Validator)             │
│                                                      │
│ Input:                                               │
│ - Reviewed text from Reviewer                        │
│ - Original context (for verification)                │
│                                                      │
│ Task:                                                │
│ "Verify all claims are supported by context.         │
│  Check citations are consistent.                     │
│  Flag unsupported claims."                           │
│                                                      │
│ LLM Call to Ollama:                                  │
│ - Model: qwen3:1.7b                                  │
│ - Temperature: 0.1 (very low for accuracy)           │
│                                                      │
│ Output:                                              │
│ Final: "Transformers are neural network              │
│ architectures that utilize self-attention            │
│ mechanisms to process sequential data [1].           │
│ Unlike RNNs, they can process all tokens             │
│ in parallel [2]..."                                  │
│                                                      │
│ Time: ~10s                                           │
└──────────────────────────────────────────────────────┘
│
▼
Return to API Gateway
```

---

## 📤 Response Flow
```
CrewAI Returns Final Summary
│
▼
┌─────────────────────────────────────────┐
│ API Gateway Post-Processing             │
│                                         │
│ 1. Output Validation (Guardrails)       │
│    - Check citation format [1], [2]     │
│    - Detect hallucination markers       │
│    - Verify length constraints          │
│    - Check for harmful content          │
│                                         │
│ 2. Response Formatting                  │
│    - Add metadata (processing time)     │
│    - Include source documents           │
│    - Format as JSON                     │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ HTTP Response                           │
│ {                                       │
│   "query": "Explain transformers",      │
│   "answer": "...",                      │
│   "sources": [                          │
│     {                                   │
│       "source": "paper1.pdf",           │
│       "chunk_index": 5,                 │
│       "content": "..."                  │
│     }                                   │
│   ],                                    │
│   "language": "en",                     │
│   "processing_time": 28.4               │
│ }                                       │
└─────────────────────────────────────────┘
│
▼
User/n8n receives response
```

---

## 🔄 n8n Workflow Flow

### Example: Daily ArXiv Digest
```
┌─────────────────────────────────────────┐
│ 1. Cron Trigger                         │
│ - Schedule: 0 9 * * * (9 AM daily)      │
│ - Activates workflow                    │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ 2. Set Variables                        │
│ - topic: "machine learning"             │
│ - max_papers: 5                         │
│ - language: "en"                        │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ 3. HTTP Request: Ingest                 │
│ POST http://api:8000/rag/ingest/arxiv   │
│ Body: {                                 │
│   "query": "{{$node.topic}}",           │
│   "max_results": {{$node.max_papers}}   │
│ }                                       │
│ Time: ~2 minutes                        │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ 4. Wait Node                            │
│ - Duration: 5 seconds                   │
│ - Ensure embeddings complete            │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ 5. HTTP Request: Query                  │
│ POST http://api:8000/research/query     │
│ Body: {                                 │
│   "query": "{{$node.topic}}",           │
│   "language": "{{$node.language}}"      │
│ }                                       │
│ Time: ~30 seconds                       │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ 6. Format Email                         │
│ - Subject: "Daily ML Digest"            │
│ - Body: Format answer as HTML           │
│ - Attach sources                        │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ 7. Send Email                           │
│ - To: user@example.com                  │
│ - SMTP server configured                │
└─────────────────────────────────────────┘
```

---

## 🔍 Error Handling Flow

### Request Validation Error
```
User Request
│
▼
API Gateway validates
│
├─ Valid → Continue
│
└─ Invalid
   │
   ▼
   Return 400 Bad Request
   {
     "detail": "Query too long (max 10000 chars)"
   }
```

### Service Unavailable Error
```
API Gateway
│
▼
Call Weaviate
│
├─ Success → Continue
│
└─ Connection Error
   │
   ├─ Retry (3 attempts)
   │  │
   │  └─ Success → Continue
   │
   └─ All retries failed
      │
      ▼
      Return 503 Service Unavailable
      {
        "detail": "Weaviate is temporarily unavailable"
      }
```

---

## 📊 Performance Optimization Points

### Bottlenecks Identified

1. **PDF Download** (50% of ingestion time)
   - Solution: Parallel downloads (future)
   - Cache downloads

2. **LLM Inference** (75% of query time)
   - Solution: GPU acceleration
   - Model quantization
   - Response caching

3. **Embedding Generation** (20% of ingestion time)
   - Solution: GPU acceleration
   - Batch processing (already implemented)

### Optimization Strategies

**Caching**:
```
Query → Check cache
│       │
│       ├─ Hit → Return cached response (< 1s)
│       │
│       └─ Miss → Process normally → Cache result
```

**Parallel Processing**:
```
Multiple ingestion requests
│
├─ Request 1 → Worker 1
├─ Request 2 → Worker 2
├─ Request 3 → Worker 3
└─ Request 4 → Queue
```

---

## 📚 Related Documentation

- **[Architecture Overview](OVERVIEW.md)** - System design
- **[Agents](AGENTS.md)** - Multi-agent details
- **[RAG Pipeline](RAG_PIPELINE.md)** - RAG implementation

---

**[⬅ Back to Architecture](README.md)**