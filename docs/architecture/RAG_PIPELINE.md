# RAG Pipeline Architecture

Detailed documentation of the Retrieval-Augmented Generation pipeline.

---

## 📋 Pipeline Overview

The RAG pipeline processes documents and retrieves relevant context for queries using hybrid search (BM25 + vector similarity).
```
┌─────────────────────────────────────────────────────────────┐
│                     RAG Pipeline                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Ingestion Path:                                            │
│  Documents → Chunking → Embedding → Weaviate                │
│                                                             │
│  Query Path:                                                │
│  Query → Embedding → Hybrid Search → Context Assembly       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📥 Document Ingestion Pipeline

### Overview
```
Source (ArXiv/Local)
    ↓
Text Extraction
    ↓
Document Processor
    ↓
Chunking (350 chars)
    ↓
Embedding Generation
    ↓
Deduplication (SHA-256)
    ↓
Weaviate Storage
```

### 1. Source Loading

**ArXiv Source** (`src/rag/sources/arxiv.py`):
```python
def fetch(self, query: str, max_results: int = 10) -> List[Document]:
    # Search ArXiv API
    # Download PDFs to data/arxiv/
    # Extract text with PyPDF
    # Create Document objects with metadata
```

**Local Source** (`src/rag/sources/local.py`):
```python
def fetch(self, pattern: str = "*") -> List[Document]:
    # Load files from data/raw/
    # Support PDF and TXT
    # Normalize metadata
```

### 2. Document Processing (`src/rag/core/processor.py`)

**Chunking Strategy**:
```python
chunk_size = 350  # characters
overlap = 50      # characters

# Chunks are created with:
# - Deterministic boundaries
# - Overlap for context
# - Metadata preservation
```

**Chunk Metadata**:
```python
{
    "document_id": "unique_hash",
    "chunk_index": 0,
    "total_chunks": 10,
    "chunk_hash": "sha256_of_content",
    "source": "filename.pdf",
    "authors": ["Author 1", "Author 2"],
    "publication_date": "2024-01-15",
    "arxiv_id": "2401.12345"
}
```

### 3. Embedding Generation (`src/rag/core/embedder.py`)

**Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Speed**: ~100 docs/second on CPU
- **Quality**: Good for general domain
```python
def embed(self, texts: List[str]) -> np.ndarray:
    # Batch embedding
    # Normalize vectors
    # Return 384-dim vectors
```

### 4. Deduplication

**Strategy**: SHA-256 content hashing
```python
def _generate_chunk_id(content: str, doc_id: str, index: int) -> str:
    # Hash content for deduplication
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"{doc_id}_{index}_{content_hash}"
```

**Benefits**:
- Prevents duplicate chunks
- Deterministic IDs (same content = same ID)
- Efficient re-ingestion

### 5. Weaviate Storage

**Schema** (explicit, no auto-schema):
```python
{
    "class": "ResearchDocument",
    "vectorizer": "none",  # We provide embeddings
    "properties": [
        {"name": "content", "dataType": ["text"]},
        {"name": "source", "dataType": ["text"]},
        {"name": "document_id", "dataType": ["text"]},
        {"name": "chunk_index", "dataType": ["int"]},
        {"name": "chunk_hash", "dataType": ["text"]},
        {"name": "authors", "dataType": ["text[]"]},
        {"name": "publication_date", "dataType": ["text"]},
        # ... more metadata fields
    ]
}
```

---

## 🔍 Query Pipeline

### Overview
```
User Query
    ↓
Query Embedding
    ↓
Hybrid Search (BM25 + Vector)
    ↓
Top-K Chunks
    ↓
Context Assembly
    ↓
Return to Agent
```

### 1. Query Embedding

Same model as document embedding:
```python
query_embedding = embedder.embed([query])[0]
# Returns 384-dim vector
```

### 2. Hybrid Search

**Retriever**: `HybridRetriever` (Haystack)
```python
retriever = HybridRetriever(
    document_store=weaviate_store,
    vector_similarity_weight=0.5,  # alpha
    bm25_weight=0.5                # (1 - alpha)
)
```

**How it works**:
1. **BM25 (Lexical)**: Keyword matching
   - Fast
   - Good for exact terms
   - Language-dependent

2. **Vector Similarity**: Semantic search
   - Understands meaning
   - Language-agnostic
   - Finds similar concepts

3. **Hybrid Score**:
```
   score = α * vector_score + (1-α) * bm25_score
```
   Default α = 0.5 (equal weight)

### 3. Result Ranking

Results sorted by hybrid score (descending).

**Top-K Selection**:
```python
top_k = 5  # Default, configurable via RAG_TOP_K
```

### 4. Context Assembly
```python
context = "\n\n".join([
    f"Source: {doc.meta['source']}\n{doc.content}"
    for doc in top_docs
])
```

**Format**:
```
Source: paper1.pdf
Content of first relevant chunk...

Source: paper2.pdf
Content of second relevant chunk...

...
```

---

## ⚙️ Configuration

### Environment Variables
```bash
# RAG Configuration (.env)
RAG_CHUNK_SIZE=350          # Chunk size in characters
RAG_CHUNK_OVERLAP=50        # Overlap between chunks
RAG_TOP_K=5                 # Number of chunks to retrieve
RAG_ALPHA=0.5               # Hybrid search alpha (0-1)

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Weaviate Connection
WEAVIATE_URL=http://weaviate:8080
```

### Tuning Parameters

**Chunk Size**:
- **Small (200-300)**: More precise, more chunks
- **Medium (350-500)**: Balanced (current)
- **Large (600-1000)**: More context, fewer chunks

**Top-K**:
- **Small (3-5)**: Focused context, faster
- **Medium (5-10)**: Balanced (current)
- **Large (10-20)**: Comprehensive, slower

**Alpha (vector weight)**:
- **Low (0.2-0.4)**: Favor keywords (BM25)
- **Medium (0.5)**: Balanced (current)
- **High (0.6-0.8)**: Favor semantics (vector)

---

## 🎯 Pipeline Optimization

### Singleton Pattern

**Problem**: Re-initializing pipeline is slow (loading models)

**Solution**: Singleton instance
```python
# src/rag/core/pipeline.py
_pipeline_instance = None

def get_rag_pipeline() -> RAGPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RAGPipeline()
    return _pipeline_instance
```

**Benefits**:
- Models loaded once
- Fast subsequent queries
- Shared across requests

### Batch Processing

Embedding generation uses batching:
```python
# Process 32 chunks at a time
batch_size = 32
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    embeddings = embedder.embed(batch)
```

### Memory Management
```python
# Proper cleanup on shutdown
def cleanup_pipeline():
    global _pipeline_instance
    if _pipeline_instance:
        _pipeline_instance.close()
        _pipeline_instance = None
```

---

## 📊 Performance Metrics

### Ingestion Performance

**Per document** (average):
- Text extraction: 1-2s
- Chunking: 100ms
- Embedding: 2-3s (CPU), 0.5s (GPU)
- Weaviate write: 500ms

**Total**: ~4-6s per paper (CPU mode)

**3 papers**: ~15-20s

### Query Performance

**Per query** (average):
- Query embedding: 100ms
- Hybrid search: 300-500ms
- Context assembly: 10ms

**Total**: ~500-600ms for retrieval

### Bottlenecks

1. **Embedding generation** (slowest)
   - **Solution**: GPU acceleration, batch processing
   
2. **PDF text extraction** (variable)
   - **Solution**: Parallel processing (future)

3. **Weaviate writes** (network I/O)
   - **Solution**: Batch writes, local deployment

---

## 🔧 Troubleshooting

### Issue: Low retrieval quality

**Symptoms**: Retrieved chunks not relevant

**Solutions**:
1. Increase `RAG_TOP_K` to retrieve more chunks
2. Adjust `RAG_ALPHA`:
   - If missing keywords → Lower alpha (favor BM25)
   - If missing concepts → Higher alpha (favor vector)
3. Check document quality (are relevant papers ingested?)

### Issue: Slow ingestion

**Symptoms**: Ingestion takes > 10s per paper

**Solutions**:
1. Enable GPU for embeddings (future)
2. Reduce batch size if OOM
3. Check network latency to Weaviate

### Issue: Duplicate chunks

**Symptoms**: Same content retrieved multiple times

**Solutions**:
1. Check deduplication is working
2. Verify chunk hashes are generated
3. Re-ingest with schema reset

---

## 🔬 Future Enhancements

### Planned
- [ ] GPU-accelerated embeddings
- [ ] Async ingestion (background jobs)
- [ ] Batch query processing
- [ ] Embedding cache (Redis)
- [ ] Multi-modal support (images, tables)

### Experimental
- [ ] HyDE (Hypothetical Document Embeddings)
- [ ] Self-RAG (adaptive retrieval)
- [ ] Graph RAG (knowledge graphs)
- [ ] Adaptive chunking (semantic boundaries)

---

## 📚 Related Documentation

- **[Architecture Overview](OVERVIEW.md)** - System design
- **[Database Schema](DATABASE.md)** - Weaviate schema
- **[Data Flow](DATA_FLOW.md)** - Request flow

---

**[⬅ Back to Architecture](README.md)**