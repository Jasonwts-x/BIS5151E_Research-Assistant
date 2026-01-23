# Python SDK Examples

Python code examples for using ResearchAssistantGPT programmatically.

## Setup
```python
# Install dependencies
import requests
import json
from pathlib import Path

# API base URL
API_URL = "http://localhost:8000"
```

---

## Basic Examples

### 1. Health Check
```python
def check_health():
    """Check API health."""
    response = requests.get(f"{API_URL}/health")
    return response.json()

# Usage
health = check_health()
print(health)  # {'status': 'ok'}
```

---

### 2. Simple Query
```python
def query_rag(question, language="en"):
    """Query the RAG system."""
    response = requests.post(
        f"{API_URL}/rag/query",
        json={
            "query": question,
            "language": language
        },
        timeout=120
    )
    response.raise_for_status()
    return response.json()

# Usage
result = query_rag("What is machine learning?")
print(result["answer"])
```

---

### 3. Ingest ArXiv Papers
```python
def ingest_arxiv(query, max_results=5):
    """Fetch and ingest papers from ArXiv."""
    response = requests.post(
        f"{API_URL}/rag/ingest/arxiv",
        json={
            "query": query,
            "max_results": max_results
        },
        timeout=300  # 5 minutes for downloads
    )
    response.raise_for_status()
    return response.json()

# Usage
result = ingest_arxiv("neural networks", max_results=10)
print(f"Ingested {result['chunks_ingested']} chunks")
```

---

## Advanced Examples

### 4. RAG Client Class
```python
class RAGClient:
    """Client for ResearchAssistant API."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health(self):
        """Check API health."""
        return self._get("/health")
    
    def ready(self):
        """Check service readiness."""
        return self._get("/ready")
    
    def query(self, question, language="en"):
        """Query with RAG and multi-agent processing."""
        return self._post("/rag/query", {
            "query": question,
            "language": language
        }, timeout=120)
    
    def ingest_local(self, pattern="*"):
        """Ingest local files."""
        return self._post("/rag/ingest/local", {
            "pattern": pattern
        }, timeout=60)
    
    def ingest_arxiv(self, query, max_results=5):
        """Ingest ArXiv papers."""
        return self._post("/rag/ingest/arxiv", {
            "query": query,
            "max_results": max_results
        }, timeout=300)
    
    def stats(self):
        """Get index statistics."""
        return self._get("/rag/stats")
    
    def reset_index(self):
        """Clear all documents (dangerous!)."""
        return self._delete("/rag/admin/reset-index")
    
    def _get(self, path):
        response = self.session.get(f"{self.base_url}{path}")
        response.raise_for_status()
        return response.json()
    
    def _post(self, path, data, timeout=30):
        response = self.session.post(
            f"{self.base_url}{path}",
            json=data,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    
    def _delete(self, path):
        response = self.session.delete(f"{self.base_url}{path}")
        response.raise_for_status()
        return response.json()

# Usage
client = RAGClient()

# Check health
print(client.health())

# Ingest papers
result = client.ingest_arxiv("transformers", max_results=5)
print(f"Ingested: {result['chunks_ingested']} chunks")

# Query
answer = client.query("Explain transformers architecture")
print(answer["answer"])
```

---

### 5. Batch Processing
```python
def batch_query(questions, language="en"):
    """Process multiple questions."""
    client = RAGClient()
    results = []
    
    for i, question in enumerate(questions, 1):
        print(f"Processing {i}/{len(questions)}: {question}")
        try:
            result = client.query(question, language)
            results.append({
                "question": question,
                "answer": result["answer"],
                "success": True
            })
        except Exception as e:
            results.append({
                "question": question,
                "error": str(e),
                "success": False
            })
    
    return results

# Usage
questions = [
    "What is machine learning?",
    "Explain neural networks",
    "What is deep learning?"
]

results = batch_query(questions)

# Save to JSON
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
```

---

### 6. Save Summary to File
```python
def save_summary(question, filename):
    """Query and save summary to file."""
    client = RAGClient()
    
    # Query
    result = client.query(question)
    
    # Save
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {question}\n\n")
        f.write(result["answer"])
        f.write("\n")
    
    print(f"Saved to: {output_path}")
    return str(output_path)

# Usage
save_summary(
    "What is retrieval augmented generation?",
    "outputs/rag_summary.md"
)
```

---

### 7. Multi-Language Support
```python
def translate_summary(question, languages=["en", "de", "fr"]):
    """Get summary in multiple languages."""
    client = RAGClient()
    results = {}
    
    for lang in languages:
        print(f"Generating {lang} summary...")
        result = client.query(question, language=lang)
        results[lang] = result["answer"]
    
    return results

# Usage
summaries = translate_summary(
    "What is machine learning?",
    languages=["en", "de", "fr", "es"]
)

# Print German version
print(summaries["de"])
```

---

### 8. Error Handling
```python
from requests.exceptions import RequestException, Timeout, HTTPError

def robust_query(question, max_retries=3):
    """Query with retry logic."""
    client = RAGClient()
    
    for attempt in range(1, max_retries + 1):
        try:
            return client.query(question)
        
        except Timeout:
            print(f"Attempt {attempt}: Timeout")
            if attempt == max_retries:
                raise
            time.sleep(5 * attempt)  # Exponential backoff
        
        except HTTPError as e:
            if e.response.status_code == 503:
                print(f"Attempt {attempt}: Service unavailable")
                if attempt == max_retries:
                    raise
                time.sleep(10)
            else:
                raise
        
        except RequestException as e:
            print(f"Attempt {attempt}: {str(e)}")
            if attempt == max_retries:
                raise
            time.sleep(5)

# Usage
try:
    result = robust_query("What is AI?")
    print(result["answer"])
except Exception as e:
    print(f"Failed after retries: {e}")
```

---

### 9. Progress Monitoring
```python
import time

def ingest_with_progress(query, max_results=10):
    """Ingest with progress monitoring."""
    client = RAGClient()
    
    # Get initial stats
    initial_stats = client.stats()
    initial_count = initial_stats["document_count"]
    
    print(f"Initial document count: {initial_count}")
    print(f"Starting ingestion: {query} ({max_results} papers)")
    
    # Start ingestion
    result = client.ingest_arxiv(query, max_results)
    
    print(f"Ingestion complete:")
    print(f"  Documents loaded: {result['documents_loaded']}")
    print(f"  Chunks ingested: {result['chunks_ingested']}")
    print(f"  Chunks skipped: {result['chunks_skipped']}")
    
    # Verify final stats
    final_stats = client.stats()
    final_count = final_stats["document_count"]
    
    print(f"Final document count: {final_count}")
    print(f"Increase: +{final_count - initial_count} chunks")
    
    return result

# Usage
ingest_with_progress("large language models", max_results=5)
```

---

### 10. Async Client (asyncio)
```python
import asyncio
import aiohttp

class AsyncRAGClient:
    """Async client for parallel requests."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    async def query(self, session, question, language="en"):
        """Async query."""
        async with session.post(
            f"{self.base_url}/rag/query",
            json={"query": question, "language": language},
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def batch_query(self, questions, language="en"):
        """Process multiple questions in parallel."""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.query(session, q, language)
                for q in questions
            ]
            return await asyncio.gather(*tasks)

# Usage
async def main():
    client = AsyncRAGClient()
    
    questions = [
        "What is machine learning?",
        "Explain neural networks",
        "What is deep learning?"
    ]
    
    results = await client.batch_query(questions)
    
    for q, r in zip(questions, results):
        print(f"Q: {q}")
        print(f"A: {r['answer'][:100]}...")
        print()

# Run
asyncio.run(main())
```

---

## Integration Examples

### 11. Jupyter Notebook Integration
```python
# Install in notebook
!pip install requests ipywidgets

from IPython.display import Markdown, display
import ipywidgets as widgets

# Create UI
question_input = widgets.Text(
    placeholder='Enter your question',
    description='Question:',
    style={'description_width': 'initial'}
)

button = widgets.Button(description='Query')
output = widgets.Output()

def on_button_click(b):
    with output:
        output.clear_output()
        display(Markdown("**Processing...**"))
        
        client = RAGClient()
        result = client.query(question_input.value)
        
        output.clear_output()
        display(Markdown(f"### Answer\n\n{result['answer']}"))

button.on_click(on_button_click)

# Display UI
display(question_input, button, output)
```

---

### 12. Pandas Integration
```python
import pandas as pd

def create_research_dataframe(questions):
    """Create DataFrame with questions and answers."""
    client = RAGClient()
    
    data = []
    for question in questions:
        try:
            result = client.query(question)
            data.append({
                'question': question,
                'answer': result['answer'],
                'answer_length': len(result['answer']),
                'status': 'success'
            })
        except Exception as e:
            data.append({
                'question': question,
                'answer': None,
                'answer_length': 0,
                'status': f'error: {str(e)}'
            })
    
    df = pd.DataFrame(data)
    return df

# Usage
questions = [
    "What is AI?",
    "Explain machine learning",
    "What are neural networks?"
]

df = create_research_dataframe(questions)
df.to_csv("research_results.csv", index=False)
print(df)
```

---

**[⬆ Back to Examples](README.md)**