# TruLens Integration Guide

Set up TruLens for monitoring and evaluating RAG pipeline quality.

---

## ⚠️ Current Status

**TruLens integration is experimental.** The code has a stub implementation that logs metrics locally.

This guide shows how to enable full TruLens monitoring.

---

## What is TruLens?

TruLens is an evaluation framework for LLM applications that tracks:

- **Answer Relevance** - Does the answer address the query?
- **Context Relevance** - Is retrieved context relevant?
- **Groundedness** - Are claims supported by context?
- **Response Quality** - Overall answer quality

---

## Installation

### 1. Install TruLens
```bash
# In DevContainer or local environment
pip install trulens-eval==0.19.0

# Add to requirements.txt
echo "trulens-eval==0.19.0" >> requirements.txt
```

---

### 2. Enable in Configuration

**Edit `src/agents/runner.py`:**
```python
class CrewRunner:
    def __init__(
        self,
        enable_guardrails: bool = True,
        enable_monitoring: bool = True  # Change to True
    ):
        # ... existing code ...
        
        # TruLens will now initialize
        self.monitor = TruLensMonitor(enabled=enable_monitoring)
```

---

### 3. Start TruLens Dashboard
```bash
# In a separate terminal
python -m src.eval.trulens

# Or manually:
docker compose exec api python -c "
from src.eval.trulens import TruLensMonitor
monitor = TruLensMonitor(enabled=True)
monitor.start_dashboard()
"
```

**Access dashboard:** http://localhost:8501

---

## Configuration

### Metrics to Track

**Edit `src/eval/trulens.py` to enable full implementation:**
```python
from trulens.core import TruSession, Feedback
from trulens.providers.openai import OpenAI as TruOpenAI
from trulens.apps.custom import instrument

class TruLensMonitor:
    def __init__(self, app_id: str = "research_assistant", enabled: bool = False):
        self.app_id = app_id
        self.enabled = enabled
        
        if enabled:
            # Initialize TruSession
            self.session = TruSession()
            
            # Initialize feedback provider
            self.provider = TruOpenAI()  # Or use local model
            
            # Define feedback functions
            self.feedbacks = [
                Feedback(
                    self.provider.relevance,
                    name="Answer Relevance"
                ).on_input_output(),
                
                Feedback(
                    self.provider.context_relevance,
                    name="Context Relevance"
                ).on_input().on(context),
                
                Feedback(
                    self.provider.groundedness,
                    name="Groundedness"
                ).on_output().on(context),
            ]
            
            logger.info("TruLens monitoring enabled")
```

---

### Instrument RAG Pipeline

**Wrap pipeline calls:**
```python
from trulens.apps.custom import TruCustomApp, instrument

@instrument
def rag_query(query: str, top_k: int = 5):
    """Instrumented RAG query."""
    pipeline = RAGPipeline.from_existing()
    docs = pipeline.run(query, top_k=top_k)
    return docs

# Create TruLens app
tru_app = TruCustomApp(
    rag_query,
    app_id="rag_pipeline",
    feedbacks=monitor.feedbacks
)

# Use instrumented version
with tru_app as recording:
    result = rag_query("What is AI?")
```

---

## Usage

### Track Query
```python
from src.eval.trulens import TruLensMonitor

monitor = TruLensMonitor(enabled=True)

# Log interaction
monitor.log_interaction(
    topic="What is machine learning?",
    context=retrieved_context,
    output=final_answer,
    language="en",
    metadata={"query_id": "123", "user": "alice"}
)
```

---

### View Metrics

**In dashboard (http://localhost:8501):**

1. **Leaderboard** - Compare runs
2. **Evaluations** - Detailed scores
3. **Records** - Individual interactions
4. **Traces** - Execution flow

---

### Query Programmatically
```python
# Get metrics
metrics = monitor.get_summary()

print(f"Total interactions: {metrics['total_interactions']}")
print(f"Average context length: {metrics['avg_context_length']}")
print(f"Languages used: {metrics['languages']}")
```

---

## Feedback Functions

### Built-in Feedbacks

**Answer Relevance:**
```python
Feedback(
    provider.relevance,
    name="Answer Relevance"
).on_input_output()
# Scores: 0.0 (irrelevant) to 1.0 (highly relevant)
```

**Context Relevance:**
```python
Feedback(
    provider.context_relevance,
    name="Context Relevance"
).on_input().on(context)
# Measures if retrieved context is relevant to query
```

**Groundedness:**
```python
Feedback(
    provider.groundedness,
    name="Groundedness"
).on_output().on(context)
# Checks if answer is supported by context
```

**Custom Feedback:**
```python
def citation_coverage(output: str) -> float:
    """Check if output has citations."""
    import re
    citations = re.findall(r'\[\d+\]', output)
    # Score based on citation count
    return min(len(citations) / 5, 1.0)  # Normalize to 0-1

Feedback(
    citation_coverage,
    name="Citation Coverage"
).on_output()
```

---

## Integration with API

### Automatic Tracking

**Update `src/api/routers/rag.py`:**
```python
from src.eval.trulens import TruLensMonitor

monitor = TruLensMonitor(enabled=True)

@router.post("/rag/query")
def query(payload: QueryRequest) -> QueryResponse:
    # ... existing query logic ...
    
    # Log to TruLens
    monitor.log_interaction(
        topic=payload.query,
        context=context_str,
        output=result["answer"],
        language=payload.language,
        metadata={"endpoint": "/rag/query"}
    )
    
    return QueryResponse(...)
```

---

## Docker Integration

### Add TruLens Service

**Create `docker/docker-compose.trulens.yml`:**
```yaml
version: '3.8'

services:
  trulens:
    image: python:3.11-slim
    container_name: trulens
    working_dir: /app
    command: python -m src.eval.trulens
    ports:
      - "8501:8501"  # Streamlit dashboard
    volumes:
      - ../src:/app/src
      - trulens_data:/app/.trulens
    networks:
      - research_net
    depends_on:
      - api
    restart: unless-stopped

volumes:
  trulens_data:
```

**Start with TruLens:**
```bash
docker compose \
  -f docker/docker-compose.yml \
  -f docker/docker-compose.trulens.yml \
  up -d
```

---

## Monitoring Best Practices

### 1. Sample Queries

Don't track every query (performance overhead):
```python
import random

if random.random() < 0.1:  # 10% sampling
    monitor.log_interaction(...)
```

---

### 2. Batch Evaluation

Evaluate periodically instead of real-time:
```python
# Collect interactions
interactions = []

def query(q):
    result = rag_pipeline(q)
    interactions.append({
        "query": q,
        "context": result.context,
        "answer": result.answer
    })
    return result

# Evaluate batch later
for interaction in interactions:
    monitor.log_interaction(**interaction)
```

---

### 3. Alert on Low Scores
```python
metrics = monitor.get_summary()

if metrics.get('avg_relevance', 1.0) < 0.7:
    logger.warning("Low relevance score detected!")
    # Send alert (email, Slack, etc.)
```

---

## Performance Impact

**Overhead:**
- Per query: +2-5 seconds (with full evaluation)
- Storage: ~1MB per 100 queries
- CPU: Moderate (feedback functions run LLM calls)

**Mitigation:**
- Use sampling (10-20% of queries)
- Run evaluations asynchronously
- Batch evaluations offline

---

## Alternatives

### Lightweight Alternatives

**1. Simple Logging:**
```python
import logging

logger.info("Query: %s, Answer length: %d, Citations: %d",
    query, len(answer), answer.count('['))
```

**2. Prometheus + Grafana:**
```python
from prometheus_client import Counter, Histogram

query_counter = Counter('queries_total', 'Total queries')
query_duration = Histogram('query_duration', 'Query duration')

@query_duration.time()
def query(q):
    query_counter.inc()
    return rag_pipeline(q)
```

---

## Troubleshooting

### Issue: TruLens Won't Start

**Check installation:**
```bash
pip show trulens-eval
# Should show version 0.19.0
```

**Reinstall:**
```bash
pip uninstall trulens-eval
pip install trulens-eval==0.19.0
```

---

### Issue: Dashboard Not Loading

**Check port:**
```bash
# Default: 8501
# Change if conflict:
streamlit run app.py --server.port 8502
```

---

### Issue: High Memory Usage

**Solution:**
```python
# Limit stored records
session.reset()  # Clear old records

# Or use SQLite backend instead of in-memory
session = TruSession(database_url="sqlite:///trulens.db")
```

---

## Resources

- **TruLens Documentation:** https://www.trulens.org/
- **TruLens GitHub:** https://github.com/truera/trulens
- **Examples:** https://www.trulens.org/trulens_eval/getting_started/quickstarts/

---

**[⬅ Back to Setup](README.md)** | **[⬆ Back to Main README](../../README.md)**