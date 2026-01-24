# RAG Pipeline Architecture

Detailed documentation of the Retrieval-Augmented Generation pipeline.

---

## Overview

The RAG pipeline handles:
1. **Document ingestion** - Loading and processing documents
2. **Chunking** - Splitting text into manageable pieces
3. **Embedding** - Converting text to vectors
4. **Retrieval** - Finding relevant chunks
5. **Context formatting** - Preparing context for LLM

---

## Pipeline Components

### 1. Ingestion Engine

**Location:** `src/rag/ingestion/engine.py`

**Responsibilities:**
- Orchestrate ingestion workflow
- Handle multiple data sources
- Manage errors and retries
- Track ingestion metrics

**Flow:**
```python
IngestionEngine
  ├─ Load documents from source
  ├─ Process each document
  │  ├─ Extract text
  │  ├─ Chunk text
  │  ├─ Generate embeddings
  │  └─ Check for duplicates
  ├─ Write to Weaviate
  └─ Return statistics
```

**Code example:**
```python
from src.rag.ingestion import IngestionEngine
from src.rag.sources import ArXivSource

engine = IngestionEngine()
source = ArXivSource()

result = engine.ingest_from_source(
    source,
    query="machine learning",
    max_results=5
)

print(f"Ingested {result.chunks_ingested} chunks")
```

---

### 2. Document Sources

**Location:** `src/rag/sources/`

#### Base Source
```python
class DocumentSource(ABC):
    @abstractmethod
    def fetch(self, **kwargs) -> List[Document]:
        """Fetch documents from source."""
        pass
```

#### ArXiv Source

**File:** `src/rag/sources/arxiv.py`

**Features:**
- Searches ArXiv API
- Downloads PDFs
- Extracts metadata (title, authors, abstract, date, categories)
- Saves to `data/arxiv/`

**Metadata structure:**
```python
{
    "source": "arxiv-2301.12345-paper-title.pdf",
    "title": "Attention Is All You Need",
    "authors": ["Vaswani et al."],
    "abstract": "The dominant sequence transduction...",
    "published": "2017-06-12",
    "categories": ["cs.CL", "cs.LG"],
    "arxiv_id": "1706.03762"
}
```

#### Local File Source

**File:** `src/rag/sources/local.py`

**Features:**
- Reads from `data/raw/`
- Supports: PDF, TXT
- Glob pattern matching
- Minimal metadata

**Example:**
```python
from src.rag.sources import LocalFileSource

source = LocalFileSource("data/raw")
docs = source.fetch(pattern="*.pdf")
```

---

### 3. Document Processor

**Location:** `src/rag/ingestion/processor.py`

**Responsibilities:**
- Text extraction from PDFs
- Text chunking
- Chunk ID generation
- Deduplication

#### Chunking Strategy

**Method:** Fixed-size chunks with overlap

**Parameters:**
```python
CHUNK_SIZE = 500      # Characters per chunk
CHUNK_OVERLAP = 50    # Overlap between chunks
```

**Why 500 characters?**
- Fits well within embedding model context (512 tokens)
- Small enough for precise retrieval
- Large enough for meaningful context
- Empirically tested for best results

**Algorithm:**
```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap  # Overlap for context continuity
    
    return chunks
```

**Example:**
```
Original text: "Machine learning is a subset of AI. It enables systems to learn..."

Chunk 1: "Machine learning is a subset of AI. It enables systems to learn from data without explicit programming. The key idea is..."

Chunk 2: "...without explicit programming. The key idea is to use algorithms that improve automatically through experience..."
         ↑ 50-char overlap
```

#### Chunk ID Generation

**Method:** Content-based hashing for deduplication
```python
def generate_chunk_id(content: str, source: str, index: int) -> str:
    """
    Generate deterministic chunk ID for deduplication.
    
    Uses SHA-256 hash of content to ensure:
    - Same content = same ID (deduplication)
    - Different content = different ID
    - Deterministic across runs
    """
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"{source}_{index}_{content_hash}"
```

**Benefits:**
- Re-ingesting same document skips existing chunks
- Deterministic IDs for reproducibility
- No duplicate storage

---

### 4. Embedding Generation

**Model:** `sentence-transformers/all-MiniLM-L6-v2`

**Specifications:**
- Dimensions: 384
- Max sequence length: 256 tokens (~512 characters)
- Speed: ~100 chunks/second (CPU)
- Quality: Good for semantic search

**Why this model?**
- ✅ Fast inference on CPU
- ✅ Good multilingual support
- ✅ Balanced quality/speed tradeoff
- ✅ Open-source

**Code:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("Your text here")
# Returns: numpy array of shape (384,)
```

**Batch processing:**
```python
# Efficient batch embedding
chunks = ["chunk 1", "chunk 2", ..., "chunk N"]
embeddings = model.encode(chunks, batch_size=32, show_progress_bar=True)
# Returns: numpy array of shape (N, 384)
```

---

### 5. Weaviate Storage

**Schema Definition:**
```python
{
    "class": "ResearchDocument",
    "description": "Research document chunks with embeddings",
    "vectorizer": "none",  # We provide embeddings manually
    "properties": [
        {
            "name": "content",
            "dataType": ["text"],
            "description": "Document chunk content"
        },
        {
            "name": "source",
            "dataType": ["text"],
            "description": "Source file path",
            "indexFilterable": True  # Enable filtering by source
        },
        {
            "name": "chunk_index",
            "dataType": ["int"],
            "description": "Chunk position in document"
        },
        {
            "name": "chunk_hash",
            "dataType": ["text"],
            "description": "Content hash for deduplication",
            "indexFilterable": True
        }
    ]
}
```

**Write operation:**
```python
client.data_object.create(
    class_name="ResearchDocument",
    data_object={
        "content": chunk_text,
        "source": "arxiv-2301.12345.pdf",
        "chunk_index": 5,
        "chunk_hash": "a1b2c3d4e5f6..."
    },
    vector=embedding.tolist()  # 384-dim vector
)
```

**Deduplication check:**
```python
# Check if chunk already exists
existing = client.data_object.get(
    class_name="ResearchDocument",
    where={
        "path": ["chunk_hash"],
        "operator": "Equal",
        "valueText": chunk_hash
    }
)

if existing["totalResults"] > 0:
    print("Chunk already exists, skipping...")
```

---

### 6. Hybrid Retrieval

**Strategy:** Combine BM25 (keyword) + Vector (semantic) search

**Why hybrid?**
- **BM25**: Catches exact keyword matches
- **Vector**: Understands semantic similarity
- **Combined**: Best of both worlds

**Algorithm:**
```python
def hybrid_search(query: str, top_k: int = 5, alpha: float = 0.5):
    """
    Hybrid search combining BM25 and vector similarity.
    
    Args:
        query: Search query
        top_k: Number of results
        alpha: Balance factor (0=BM25 only, 1=vector only, 0.5=balanced)
    """
    # Generate query embedding
    query_embedding = embedder.encode(query)
    
    # Weaviate hybrid search
    results = client.query.get(
        "ResearchDocument",
        ["content", "source", "chunk_index"]
    ).with_hybrid(
        query=query,              # BM25 search
        vector=query_embedding,   # Vector search
        alpha=alpha               # Balance factor
    ).with_limit(top_k).do()
    
    return results
```

**Alpha parameter:**
- `0.0` = Pure BM25 (keyword matching)
- `0.5` = Balanced (default)
- `1.0` = Pure vector (semantic)

**Example results:**

Query: "transformer architecture"
```
BM25 alone (alpha=0):
1. "The Transformer architecture uses self-attention..." (exact match)
2. "Architecture of modern transformers includes..." (exact match)
3. "Neural network architectures have evolved..." (partial match)

Vector alone (alpha=1):
1. "Attention mechanisms enable models to focus..." (semantic)
2. "Self-attention layers process sequences..." (semantic)
3. "Encoder-decoder models like BERT..." (semantic)

Hybrid (alpha=0.5):
1. "The Transformer architecture uses self-attention..." (both)
2. "Attention mechanisms enable models to focus..." (semantic)
3. "Architecture of modern transformers includes..." (keyword)
```

**Current setting:** `alpha=0.75` (favor semantic search)

---

## Pipeline Performance

### Ingestion Performance

**Single document (10 pages, ~5000 words):**
```
Text extraction:    500ms
Chunking:          10ms
Embedding:         200ms (10 chunks × 20ms)
Weaviate write:    100ms
Total:             ~810ms
```

**Batch ingestion (5 papers):**
```
PDF downloads:     15-20s
Processing:        4-5s
Total:             ~20-25s
```

**Bottlenecks:**
1. PDF download (network I/O)
2. Embedding generation (CPU-bound)
3. Weaviate writes (I/O)

### Retrieval Performance

**Query latency breakdown:**
```
Query embedding:    20ms
Hybrid search:      200-500ms
Result formatting:  10ms
Total:             ~250-550ms
```

**Factors affecting speed:**
- Index size (more docs = slower)
- Query complexity
- top_k value (more results = slower)

---

## Error Handling

### Common Errors

**1. PDF extraction failure**
```python
try:
    text = extract_text_from_pdf(file_path)
except PDFReadError:
    logger.error(f"Failed to read PDF: {file_path}")
    # Skip document or try OCR
```

**2. Embedding generation failure**
```python
try:
    embeddings = model.encode(chunks)
except Exception as e:
    logger.error(f"Embedding failed: {e}")
    # Retry with smaller batch
```

**3. Weaviate connection error**
```python
try:
    client.data_object.create(...)
except WeaviateException as e:
    if "already exists" in str(e):
        logger.info("Chunk already exists, skipping")
    else:
        raise
```

### Retry Logic
```python
@retry(tries=3, delay=1, backoff=2)
def write_to_weaviate(chunk, embedding):
    """Write with exponential backoff retry."""
    client.data_object.create(
        class_name="ResearchDocument",
        data_object=chunk,
        vector=embedding
    )
```

---

## Optimization Techniques

### 1. Batch Processing

**Instead of:**
```python
for chunk in chunks:
    embedding = model.encode(chunk)
    write_to_weaviate(chunk, embedding)
```

**Do:**
```python
# Batch embed (much faster)
embeddings = model.encode(chunks, batch_size=32)

# Batch write (fewer network calls)
client.batch.configure(batch_size=100)
with client.batch as batch:
    for chunk, embedding in zip(chunks, embeddings):
        batch.add_data_object(chunk, vector=embedding)
```

### 2. Caching
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str):
    """Cache embeddings for frequently seen text."""
    return model.encode(text)
```

### 3. Parallel Processing
```python
from concurrent.futures import ThreadPoolExecutor

def process_documents_parallel(documents):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(process_document, documents)
    return list(results)
```

---

## Configuration

**File:** `configs/app.yaml`
```yaml
rag:
  chunk_size: 500
  chunk_overlap: 50
  top_k: 5
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  
weaviate:
  host: "weaviate"
  port: 8080
  class_name: "ResearchDocument"
  
retrieval:
  hybrid_alpha: 0.75  # Favor semantic search
  use_reranking: false  # Future feature
```

---

## Future Improvements

### Planned

1. **Adaptive chunking** - Respect sentence/paragraph boundaries
2. **Metadata filtering** - Filter by date, author, category
3. **Reranking** - Add cross-encoder reranking after retrieval
4. **Query expansion** - Automatically expand queries for better retrieval
5. **Embedding caching** - Cache embeddings in Redis

### Research

1. **HyDE (Hypothetical Document Embeddings)** - Generate hypothetical answer, embed it
2. **ColBERT** - Late interaction retrieval
3. **SPLADE** - Sparse-dense hybrid
4. **Graph RAG** - Build knowledge graphs

---

## Debugging

### View indexed documents
```python
from weaviate import Client

client = Client("http://localhost:8080")

# Get all documents
results = client.query.get(
    "ResearchDocument",
    ["content", "source", "chunk_index"]
).with_limit(100).do()

for doc in results["data"]["Get"]["ResearchDocument"]:
    print(f"{doc['source']} - Chunk {doc['chunk_index']}")
    print(doc['content'][:100] + "...")
    print()
```

### Test retrieval
```python
from src.rag.core import RAGPipeline

pipeline = RAGPipeline.from_existing()

# Test query
docs = pipeline.run("What is machine learning?", top_k=3)

for i, doc in enumerate(docs, 1):
    print(f"\n=== Result {i} ===")
    print(f"Source: {doc.meta['source']}")
    print(f"Score: {doc.score}")
    print(f"Content: {doc.content[:200]}...")
```

---

**[⬅ Back to Architecture](README.md)** | **[⬆ Back to Main README](../../README.md)**