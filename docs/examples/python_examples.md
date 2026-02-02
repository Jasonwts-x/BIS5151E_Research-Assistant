# Python Integration Examples

Complete Python examples for integrating ResearchAssistantGPT.

---

## 📋 Table of Contents

- [Simple Client](#simple-client)
- [Application Integration](#application-integration)
- [Async Client](#async-client)
- [Error Handling](#error-handling)
- [Web Integration](#web-integration)

---

## 🚀 Simple Client

### Basic Usage
```python
import requests
from typing import Dict, List, Any

class ResearchAssistant:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def ingest_arxiv(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """Ingest papers from ArXiv."""
        response = requests.post(
            f"{self.base_url}/rag/ingest/arxiv",
            json={"query": query, "max_results": max_results}
        )
        response.raise_for_status()
        return response.json()
    
    def ingest_local(self, pattern: str = "*") -> Dict[str, Any]:
        """Ingest local files."""
        response = requests.post(
            f"{self.base_url}/rag/ingest/local",
            json={"pattern": pattern}
        )
        response.raise_for_status()
        return response.json()
    
    def research_query(self, query: str, language: str = "en", top_k: int = 5) -> Dict[str, Any]:
        """Execute complete research workflow."""
        response = requests.post(
            f"{self.base_url}/research/query",
            json={"query": query, "language": language, "top_k": top_k}
        )
        response.raise_for_status()
        return response.json()
    
    def rag_query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Query documents without agent processing."""
        response = requests.post(
            f"{self.base_url}/rag/query",
            json={"query": query, "top_k": top_k}
        )
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        response = requests.get(f"{self.base_url}/rag/stats")
        response.raise_for_status()
        return response.json()

# Usage
if __name__ == "__main__":
    client = ResearchAssistant()
    
    # Ingest papers
    print("Ingesting papers...")
    result = client.ingest_arxiv("machine learning", max_results=3)
    print(f"✅ Ingested {result['documents_loaded']} papers")
    
    # Query
    print("\nQuerying...")
    result = client.research_query("What is machine learning?")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nSources: {len(result['sources'])}")
```

---

## 🏗️ Application Integration

### Flask Web Application
```python
from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

class ResearchClient:
    BASE_URL = "http://localhost:8000"
    
    @staticmethod
    def research_query(query: str, language: str = "en"):
        response = requests.post(
            f"{ResearchClient.BASE_URL}/research/query",
            json={"query": query, "language": language},
            timeout=60
        )
        response.raise_for_status()
        return response.json()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def query():
    data = request.get_json()
    query = data.get('query')
    language = data.get('language', 'en')
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    try:
        result = ResearchClient.research_query(query, language)
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    try:
        response = requests.get(f"{ResearchClient.BASE_URL}/rag/stats")
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**HTML Template** (`templates/index.html`):
```html
<!DOCTYPE html>
<html>
<head>
    <title>Research Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; }
        textarea { width: 100%; height: 100px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
        #result { margin-top: 20px; padding: 20px; background: #f5f5f5; }
    </style>
</head>
<body>
    <h1>Research Assistant</h1>
    <textarea id="query" placeholder="Enter your research question..."></textarea>
    <br><br>
    <button onclick="submitQuery()">Submit</button>
    
    <div id="result" style="display:none;">
        <h3>Answer:</h3>
        <div id="answer"></div>
        <h4>Sources:</h4>
        <div id="sources"></div>
    </div>
    
    <script>
        async function submitQuery() {
            const query = document.getElementById('query').value;
            const resultDiv = document.getElementById('result');
            const answerDiv = document.getElementById('answer');
            const sourcesDiv = document.getElementById('sources');
            
            if (!query) {
                alert('Please enter a query');
                return;
            }
            
            answerDiv.innerHTML = 'Processing...';
            resultDiv.style.display = 'block';
            sourcesDiv.innerHTML = '';
            
            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query, language: 'en'})
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    answerDiv.innerHTML = data.answer;
                    sourcesDiv.innerHTML = data.sources.map(s => 
                        `<p>[${s.index}] ${s.source}<br>
                        <small>${s.authors.join(', ')} (${s.publication_date})</small></p>`
                    ).join('');
                } else {
                    answerDiv.innerHTML = `Error: ${data.error}`;
                }
            } catch (error) {
                answerDiv.innerHTML = `Error: ${error.message}`;
            }
        }
    </script>
</body>
</html>
```

---

## ⚡ Async Client

### Using `aiohttp`
```python
import asyncio
import aiohttp
from typing import Dict, List, Any

class AsyncResearchAssistant:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def ingest_arxiv(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """Ingest papers from ArXiv asynchronously."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/rag/ingest/arxiv",
                json={"query": query, "max_results": max_results}
            ) as response:
                response.raise_for_status()
                return await response.json()
    
    async def research_query(self, query: str, language: str = "en") -> Dict[str, Any]:
        """Execute research query asynchronously."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/research/query",
                json={"query": query, "language": language},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response.raise_for_status()
                return await response.json()
    
    async def batch_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple queries in parallel."""
        tasks = [self.research_query(q) for q in queries]
        return await asyncio.gather(*tasks)

# Usage
async def main():
    client = AsyncResearchAssistant()
    
    # Single query
    result = await client.research_query("What is machine learning?")
    print(f"Answer: {result['answer']}")
    
    # Batch queries
    queries = [
        "What are neural networks?",
        "Explain deep learning",
        "What is reinforcement learning?"
    ]
    results = await client.batch_queries(queries)
    
    for query, result in zip(queries, results):
        print(f"\nQ: {query}")
        print(f"A: {result['answer'][:200]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🛡️ Error Handling

### Comprehensive Error Handling
```python
import requests
from typing import Dict, Any, Optional
import time

class RobustResearchClient:
    def __init__(self, base_url: str = "http://localhost:8000", retries: int = 3):
        self.base_url = base_url
        self.retries = retries
    
    def _request_with_retry(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retries):
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except requests.exceptions.ConnectionError as e:
                if attempt < self.retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Connection error. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Failed to connect after {self.retries} attempts: {e}")
            
            except requests.exceptions.Timeout as e:
                if attempt < self.retries - 1:
                    print(f"Request timeout. Retrying...")
                    time.sleep(2)
                else:
                    raise Exception(f"Request timed out after {self.retries} attempts: {e}")
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 503:  # Service Unavailable
                    if attempt < self.retries - 1:
                        print("Service unavailable. Retrying...")
                        time.sleep(5)
                    else:
                        raise Exception("Service is unavailable")
                else:
                    raise  # Don't retry other HTTP errors
    
    def research_query(self, query: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """Execute research query with error handling."""
        try:
            # Validate input
            if not query or len(query) > 10000:
                raise ValueError("Query must be between 1 and 10000 characters")
            
            # Make request
            response = self._request_with_retry(
                "POST",
                "/research/query",
                json={"query": query, "language": language},
                timeout=60
            )
            
            return response.json()
            
        except ValueError as e:
            print(f"❌ Validation error: {e}")
            return None
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

# Usage
if __name__ == "__main__":
    client = RobustResearchClient()
    
    result = client.research_query("What is AI?")
    if result:
        print(f"✅ Success: {result['answer'][:100]}...")
    else:
        print("❌ Query failed")
```

---

## 🌐 Web Integration

### FastAPI Backend
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from typing import Optional

app = FastAPI(title="Research Assistant Frontend")

# CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    language: str = "en"
    top_k: Optional[int] = 5

class IngestRequest(BaseModel):
    query: str
    max_results: int = 3

BACKEND_URL = "http://localhost:8000"

@app.post("/api/research")
async def research(request: QueryRequest):
    """Execute research query."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/research/query",
            json={
                "query": request.query,
                "language": request.language,
                "top_k": request.top_k
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest")
async def ingest(request: IngestRequest):
    """Ingest papers from ArXiv."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/rag/ingest/arxiv",
            json={
                "query": request.query,
                "max_results": request.max_results
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def stats():
    """Get index statistics."""
    try:
        response = requests.get(f"{BACKEND_URL}/rag/stats")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return {"status": "healthy", "backend": response.json()}
    except:
        return {"status": "unhealthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

## 📦 Complete Package Example

### `research_client` Package

**`research_client/__init__.py`**:
```python
from .client import ResearchAssistant
from .async_client import AsyncResearchAssistant

__version__ = "1.0.0"
__all__ = ["ResearchAssistant", "AsyncResearchAssistant"]
```

**`research_client/client.py`**:
```python
import requests
from typing import Dict, Any, List
from .exceptions import APIError, ConnectionError, ValidationError

class ResearchAssistant:
    """Synchronous client for ResearchAssistantGPT."""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 60):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to {url}: {e}")
        except requests.exceptions.Timeout:
            raise ConnectionError(f"Request to {url} timed out")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                raise ValidationError(e.response.json().get("detail", "Validation error"))
            raise APIError(f"API error: {e}")
    
    def ingest_arxiv(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """Ingest papers from ArXiv."""
        return self._request("POST", "/rag/ingest/arxiv", json={
            "query": query,
            "max_results": max_results
        })
    
    def research_query(self, query: str, language: str = "en", top_k: int = 5) -> Dict[str, Any]:
        """Execute complete research workflow."""
        return self._request("POST", "/research/query", json={
            "query": query,
            "language": language,
            "top_k": top_k
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return self._request("GET", "/rag/stats")
    
    def close(self):
        """Close session."""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
```

**`research_client/exceptions.py`**:
```python
class ResearchClientError(Exception):
    """Base exception for research client."""
    pass

class APIError(ResearchClientError):
    """API returned an error."""
    pass

class ConnectionError(ResearchClientError):
    """Failed to connect to API."""
    pass

class ValidationError(ResearchClientError):
    """Invalid input."""
    pass
```

**Usage**:
```python
from research_client import ResearchAssistant

# Context manager
with ResearchAssistant() as client:
    result = client.research_query("What is AI?")
    print(result['answer'])

# Regular usage
client = ResearchAssistant()
try:
    result = client.research_query("What is AI?")
    print(result['answer'])
finally:
    client.close()
```

---

## 📚 Related Documentation

- **[Basic Usage](BASIC_USAGE.md)** - Simple examples
- **[n8n Setup & Workflows](../setup/N8N.md)** - Automation
- **[API Reference](../api/ENDPOINTS.md)** - All endpoints

---

**[⬅ Back to Examples](README.md)**