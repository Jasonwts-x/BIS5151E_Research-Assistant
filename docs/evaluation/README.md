# Evaluation System Documentation

ResearchAssistantGPT includes a comprehensive evaluation system for monitoring quality, safety, and performance.

---

## Overview

The evaluation system consists of four main components:

1. **TruLens** - Quality metrics (groundedness, relevance)
2. **Guardrails** - Safety validation (input/output checks)
3. **Performance** - Timing and resource tracking
4. **Quality Metrics** - ROUGE, BLEU, semantic similarity

---

## Architecture
```
┌──────────────────────────────────────────┐
│ CrewAI Service (Port 8100)               │
│  ├─ Input Validation (Guardrails)        │
│  ├─ RAG Retrieval (Performance Tracked)  │
│  ├─ Agent Execution (Performance Tracked)│
│  ├─ Output Validation (Guardrails)       │
│  └─ TruLens Evaluation                   │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│ Evaluation Service (Ports 8501/8502)     │
│  ├─ PostgreSQL Storage                   │
│  ├─ Metrics API (8502)                   │
│  └─ Streamlit Dashboard (8501)           │
└──────────────────────────────────────────┘
```

---

## Components

### 1. TruLens Integration

**Location:** `src/eval/trulens/`

**Metrics:**
- **Groundedness** (0-1): Are claims supported by context?
- **Answer Relevance** (0-1): Does answer address the query?
- **Context Relevance** (0-1): Is retrieved context relevant?
- **Citation Quality** (0-1): Are sources properly cited?

**Usage:**
```python
from src.eval.trulens import TruLensClient

client = TruLensClient(enabled=True)
result = client.evaluate(
    query="What is AI?",
    context="Retrieved context...",
    answer="AI is artificial intelligence...",
)

print(f"Groundedness: {result['trulens']['groundedness']}")
```

---

### 2. Guardrails Validation

**Location:** `src/eval/guardrails/`

**Input Validators:**
- Jailbreak Detection
- PII Detection
- Topic Relevance Check

**Output Validators:**
- Citation Format Validation
- Hallucination Detection
- Length Validation
- Harmful Content Detection

**Usage:**
```python
from src.eval.guardrails import InputValidator, OutputValidator

input_validator = InputValidator()
output_validator = OutputValidator()

# Validate input
passed, results = input_validator.validate("User query here")
if not passed:
    print("Input validation failed!")

# Validate output
passed, results = output_validator.validate("Generated answer here")
if not passed:
    print("Output validation failed!")
```

---

### 3. Performance Monitoring

**Location:** `src/eval/performance/`

**Tracked Metrics:**
- Total execution time
- RAG retrieval time
- Agent execution time (per agent)
- LLM inference time
- Guardrails validation time

**Usage:**
```python
from src.eval.performance import PerformanceTracker

tracker = PerformanceTracker()
tracker.start()

with tracker.track("rag_retrieval"):
    # ... RAG code ...
    pass

with tracker.track("agent_writer"):
    # ... agent code ...
    pass

tracker.stop()
summary = tracker.get_summary()
print(f"Total time: {summary['total_time']}s")
```

---

### 4. Quality Metrics

**Location:** `src/eval/quality/`

**Available Calculators:**
- **ROUGE** - N-gram overlap (ROUGE-1, ROUGE-2, ROUGE-L)
- **BLEU** - Precision-based scoring
- **Semantic Similarity** - Embedding-based relevance
- **Factuality Checker** - Claim verification

**Usage:**
```python
from src.eval.quality import ROUGECalculator

calculator = ROUGECalculator()
scores = calculator.calculate(
    generated="Generated answer",
    reference="Reference answer",
)

print(f"ROUGE-1: {scores['rouge-1']}")
print(f"ROUGE-2: {scores['rouge-2']}")
```

---

## Dashboard

Access the evaluation dashboard at **http://localhost:8501**

**Features:**
- Real-time metrics overview
- Performance timing breakdown
- Quality score trends
- Guardrails violation tracking
- Evaluation leaderboard

---

## API Endpoints

**Base URL:** `http://localhost:8502`

### Evaluate Query/Answer
```bash
POST /metrics/evaluate
{
  "query": "What is AI?",
  "answer": "AI is artificial intelligence...",
  "context": "Retrieved context...",
  "language": "en"
}
```

### Get Leaderboard
```bash
GET /metrics/leaderboard?limit=100
```

### Get Record Details
```bash
GET /metrics/record/{record_id}
```

---

## Configuration

**Environment Variables:**
```bash
# Enable/disable evaluation
TRULENS_ENABLED=true
GUARDRAILS_ENABLED=true

# Guardrails settings
GUARDRAILS_STRICT_MODE=false

# Database
TRULENS_DATABASE_URL=postgresql://user:pass@postgres:5432/trulens
```

---

## Database Schema

Evaluation data is stored in PostgreSQL with the following tables:

- `records` - TruLens evaluation records
- `feedback_results` - TruLens feedback scores
- `performance_metrics` - Timing and resource data
- `quality_metrics` - ROUGE/BLEU scores
- `guardrails_results` - Validation results

See `scripts/setup/init-db.sql` for full schema.

---

## Best Practices

1. **Always enable guardrails** in production
2. **Monitor dashboard regularly** for quality degradation
3. **Set up alerts** for low groundedness scores
4. **Review violations** caught by guardrails
5. **Track performance trends** over time

---

## Troubleshooting

**Dashboard not loading:**
```bash
# Check if eval service is running
docker compose ps eval

# Check logs
docker compose logs eval
```

**No evaluation data:**
```bash
# Ensure TruLens is enabled
docker compose exec eval env | grep TRULENS_ENABLED

# Check database connection
docker compose exec eval python -c "from src.eval.trulens import TruLensClient; TruLensClient(enabled=True)"
```

---

## Further Reading

- [TruLens Documentation](https://www.trulens.org/)
- [Guardrails AI Documentation](https://www.guardrailsai.com/)
- [ROUGE Score Explanation](https://en.wikipedia.org/wiki/ROUGE_(metric))
- [BLEU Score Explanation](https://en.wikipedia.org/wiki/BLEU)