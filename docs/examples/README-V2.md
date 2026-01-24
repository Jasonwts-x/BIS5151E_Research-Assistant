# Usage Examples

Practical examples and code snippets for ResearchAssistantGPT.

---

## 📚 Example Categories

| Category | Description |
|----------|-------------|
| [**Python Examples**](#python-examples) | Using the system from Python |
| [**API Examples**](#api-examples) | REST API calls with cURL |
| [**n8n Workflows**](workflow_examples.md) | Automation workflows |
| [**CLI Examples**](#cli-examples) | Command-line tools |

---

## Python Examples

### Basic Query
```python
import requests

# Query the system
response = requests.post(
    "http://localhost:8000/rag/query",
    json={
        "query": "What is machine learning?",
        "language": "en"
    }
)

result = response.json()
print(result["answer"])
```

### Ingest and Query
```python
import requests
import time

# Step 1: Ingest papers
ingest_response = requests.post(
    "http://localhost:8000/rag/ingest/arxiv",
    json={
        "query": "transformer architecture",
        "max_results": 5
    }
)

print(f"Ingested {ingest_response.json()['chunks_ingested']} chunks")

# Step 2: Wait for ingestion to complete
time.sleep(5)

# Step 3: Query
query_response = requests.post(
    "http://localhost:8000/rag/query",
    json={
        "query": "Explain the transformer architecture",
        "language": "en"
    }
)

print(query_response.json()["answer"])
```

### Multilingual Query
```python
import requests

languages = ["en", "de", "fr", "es"]

for lang in languages:
    response = requests.post(
        "http://localhost:8000/rag/query",
        json={
            "query": "What is deep learning?",
            "language": lang
        }
    )
    
    print(f"\n=== {lang.upper()} ===")
    print(response.json()["answer"])
```

### Error Handling
```python
import requests
from requests.exceptions import RequestException

def query_with_retry(query, max_retries=3):
    """Query with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/rag/query",
                json={"query": query, "language": "en"},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        
        except RequestException as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # Exponential backoff
                print(f"Attempt {attempt + 1} failed, retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"All retries failed: {e}")
                raise

# Usage
result = query_with_retry("What is AI?")
print(result["answer"])
```

### Batch Processing
```python
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def query_single(query):
    """Query a single question."""
    response = requests.post(
        "http://localhost:8000/rag/query",
        json={"query": query, "language": "en"}
    )
    return {
        "query": query,
        "answer": response.json()["answer"]
    }

# Batch queries
queries = [
    "What is machine learning?",
    "What is deep learning?",
    "What is reinforcement learning?"
]

# Process in parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(query_single, q) for q in queries]
    
    for future in as_completed(futures):
        result = future.result()
        print(f"\nQ: {result['query']}")
        print(f"A: {result['answer'][:200]}...")
```

### Using the Python RAG Pipeline Directly
```python
# Only works inside Docker containers or with proper environment setup
from src.rag.core import RAGPipeline
from src.rag.ingestion import IngestionEngine
from src.rag.sources import LocalFileSource

# Initialize pipeline
pipeline = RAGPipeline.from_existing()

# Ingest documents
engine = IngestionEngine()
source = LocalFileSource("data/raw")
result = engine.ingest_from_source(source, pattern="*.pdf")

print(f"Ingested: {result.chunks_ingested} chunks")

# Query
docs = pipeline.run(query="What is AI?", top_k=5)

for i, doc in enumerate(docs, 1):
    print(f"\n=== Document {i} ===")
    print(f"Source: {doc.meta['source']}")
    print(f"Score: {doc.score:.3f}")
    print(f"Content: {doc.content[:200]}...")
```

### Statistics and Monitoring
```python
import requests

# Get index statistics
stats = requests.get("http://localhost:8000/rag/stats").json()

print(f"Total documents: {stats['total_documents']}")
print(f"Total chunks: {stats['total_chunks']}")
print(f"Index size: {stats['index_size_mb']:.2f} MB")

print("\nSources:")
for source, count in stats['sources'].items():
    print(f"  - {source}: {count} documents")
```

---

## API Examples

### Health Check
```bash
# Check API health
curl http://localhost:8000/health

# Check service readiness
curl http://localhost:8000/ready
```

### Ingest from ArXiv
```bash
# Ingest 5 papers on neural networks
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural networks",
    "max_results": 5
  }'
```

### Ingest Local Files
```bash
# Ingest all PDFs
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*.pdf"}'

# Ingest specific pattern
curl -X POST http://localhost:8000/rag/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"pattern": "paper-2024-*.pdf"}'
```

### Query
```bash
# Basic query
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is artificial intelligence?",
    "language": "en"
  }'

# German query
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Was ist künstliche Intelligenz?",
    "language": "de"
  }'

# With more context (top_k=10)
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain transformer architecture in detail",
    "language": "en",
    "top_k": 10
  }'
```

### Get Statistics
```bash
curl http://localhost:8000/rag/stats | jq
```

### Pretty Print JSON Response
```bash
# Install jq first: apt-get install jq

curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?", "language": "en"}' \
  | jq '.answer'
```

---

## CLI Examples

### Ingestion
```bash
# Access CLI inside Docker container
docker compose exec api python -m src.rag.cli --help

# Ingest local files
docker compose exec api python -m src.rag.cli ingest-local

# Ingest specific pattern
docker compose exec api python -m src.rag.cli ingest-local --pattern "arxiv*"

# Ingest from ArXiv
docker compose exec api python -m src.rag.cli ingest-arxiv "machine learning" --max-results 5
```

### Query
```bash
# Query from CLI
docker compose exec api python -m src.rag.cli query "What is deep learning?"

# With language specification
docker compose exec api python -m src.rag.cli query "Was ist KI?" --language de
```

### Statistics
```bash
# View index stats
docker compose exec api python -m src.rag.cli stats
```

### Reset Index
```bash
# ⚠️ WARNING: This deletes all data
docker compose exec api python -m src.rag.cli reset-index --yes
```

---

## JavaScript Examples

### Node.js
```javascript
const fetch = require('node-fetch');

async function query(question) {
  const response = await fetch('http://localhost:8000/rag/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: question,
      language: 'en'
    })
  });
  
  const data = await response.json();
  return data.answer;
}

// Usage
query('What is machine learning?')
  .then(answer => console.log(answer))
  .catch(err => console.error(err));
```

### Browser (Fetch API)
```html
<!DOCTYPE html>
<html>
<head>
  <title>Research Assistant</title>
</head>
<body>
  <input type="text" id="query" placeholder="Ask a question...">
  <button onclick="ask()">Ask</button>
  <div id="answer"></div>

  <script>
    async function ask() {
      const query = document.getElementById('query').value;
      const response = await fetch('http://localhost:8000/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, language: 'en' })
      });
      
      const data = await response.json();
      document.getElementById('answer').innerText = data.answer;
    }
  </script>
</body>
</html>
```

---

## Advanced Examples

### Custom Workflow: Weekly Digest
```python
import requests
from datetime import datetime, timedelta

def weekly_digest(topics):
    """
    Generate weekly digest for multiple topics.
    """
    results = []
    
    for topic in topics:
        # Query each topic
        response = requests.post(
            "http://localhost:8000/rag/query",
            json={"query": f"Recent developments in {topic}", "language": "en"}
        )
        
        results.append({
            "topic": topic,
            "summary": response.json()["answer"],
            "date": datetime.now().isoformat()
        })
    
    # Format as markdown
    report = f"# Weekly Research Digest - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    for item in results:
        report += f"## {item['topic']}\n\n"
        report += f"{item['summary']}\n\n"
        report += "---\n\n"
    
    # Save to file
    filename = f"digest_{datetime.now().strftime('%Y%m%d')}.md"
    with open(filename, 'w') as f:
        f.write(report)
    
    return filename

# Usage
topics = [
    "transformer models",
    "reinforcement learning",
    "computer vision"
]

digest_file = weekly_digest(topics)
print(f"Digest saved to {digest_file}")
```

### Comparative Analysis
```python
import requests

def compare_topics(topic1, topic2):
    """
    Compare two topics side by side.
    """
    # Query both topics
    response1 = requests.post(
        "http://localhost:8000/rag/query",
        json={"query": f"Explain {topic1}", "language": "en"}
    )
    
    response2 = requests.post(
        "http://localhost:8000/rag/query",
        json={"query": f"Explain {topic2}", "language": "en"}
    )
    
    # Format comparison
    print(f"\n{'='*60}")
    print(f"{topic1.upper()} vs {topic2.upper()}")
    print(f"{'='*60}\n")
    
    print(f"--- {topic1} ---")
    print(response1.json()["answer"])
    
    print(f"\n--- {topic2} ---")
    print(response2.json()["answer"])

# Usage
compare_topics("supervised learning", "unsupervised learning")
```

### Research Pipeline
```python
import requests
import time

def research_pipeline(main_topic, subtopics):
    """
    Complete research pipeline: ingest → query → report.
    """
    print(f"Starting research on: {main_topic}")
    
    # Step 1: Ingest relevant papers
    print("\n1. Ingesting papers...")
    ingest_response = requests.post(
        "http://localhost:8000/rag/ingest/arxiv",
        json={"query": main_topic, "max_results": 10}
    )
    
    print(f"   Ingested: {ingest_response.json()['chunks_ingested']} chunks")
    time.sleep(5)  # Wait for indexing
    
    # Step 2: Query subtopics
    print("\n2. Querying subtopics...")
    results = {}
    
    for subtopic in subtopics:
        response = requests.post(
            "http://localhost:8000/rag/query",
            json={"query": subtopic, "language": "en"}
        )
        results[subtopic] = response.json()["answer"]
        print(f"   ✓ {subtopic}")
    
    # Step 3: Generate report
    print("\n3. Generating report...")
    report = f"# Research Report: {main_topic}\n\n"
    
    for subtopic, answer in results.items():
        report += f"## {subtopic}\n\n{answer}\n\n"
    
    # Save
    filename = f"report_{main_topic.replace(' ', '_')}.md"
    with open(filename, 'w') as f:
        f.write(report)
    
    print(f"\n✓ Report saved to {filename}")
    return filename

# Usage
research_pipeline(
    main_topic="deep learning",
    subtopics=[
        "What are neural networks?",
        "What is backpropagation?",
        "What are convolutional neural networks?",
        "What are recurrent neural networks?"
    ]
)
```

---

## Testing Examples

### Unit Test Example
```python
import pytest
from src.rag.ingestion.processor import DocumentProcessor

def test_chunk_text():
    processor = DocumentProcessor()
    text = "This is a test. " * 100
    
    chunks = processor.chunk_text(text, chunk_size=200, overlap=50)
    
    assert len(chunks) > 0
    assert all(len(c) <= 200 for c in chunks)
    assert chunks[0][-50:] == chunks[1][:50]  # Overlap check
```

### Integration Test Example
```python
import pytest
import requests

def test_full_workflow():
    """Test complete ingestion and query workflow."""
    # Ingest
    ingest_response = requests.post(
        "http://localhost:8000/rag/ingest/arxiv",
        json={"query": "test query", "max_results": 1}
    )
    assert ingest_response.status_code == 200
    assert ingest_response.json()["success"] == True
    
    # Query
    query_response = requests.post(
        "http://localhost:8000/rag/query",
        json={"query": "test question", "language": "en"}
    )
    assert query_response.status_code == 200
    assert "answer" in query_response.json()
```

---

## More Examples

See also:
- [**n8n Workflow Examples**](workflow_examples.md) - Automation workflows
- [**API Reference**](../api/README.md) - Complete API documentation
- [**Architecture**](../architecture/README.md) - System internals

---

**[⬅ Back to Main README](../../README.md)**