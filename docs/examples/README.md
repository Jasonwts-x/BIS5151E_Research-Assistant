# Usage Examples

Practical examples for using ResearchAssistantGPT.

## Quick Links

- [API Usage Examples](api_usage.md)
- [n8n Workflow Examples](workflow_examples.md)
- [Python SDK Examples](python_examples.md)
- [CLI Examples](cli_examples.md)

---

## Quick Start Examples

### 1. Basic Query
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "language": "en"
  }'
```

### 2. Ingest ArXiv Papers
```bash
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural networks",
    "max_results": 5
  }'
```

### 3. Check System Health
```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

---

## Common Workflows

### Daily Research Update
```bash
#!/bin/bash
# Fetch latest papers and generate summary

# 1. Ingest new papers
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "LLM reasoning", "max_results": 3}'

# 2. Generate summary
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are recent advances in LLM reasoning?", "language": "en"}' \
  | jq -r '.answer' > daily_summary.txt
```

### Literature Review
```bash
#!/bin/bash
# Multi-topic literature review

topics=("transformers" "attention mechanisms" "few-shot learning")

for topic in "${topics[@]}"; do
  echo "Processing: $topic"
  
  # Ingest
  curl -X POST http://localhost:8000/rag/ingest/arxiv \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$topic\", \"max_results\": 5}"
  
  # Query
  curl -X POST http://localhost:8000/rag/query \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"Summarize research on $topic\", \"language\": \"en\"}" \
    | jq -r '.answer' > "${topic}_summary.txt"
done
```

---

## Language Examples

### English Summary
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain retrieval augmented generation",
    "language": "en"
  }'
```

### German Summary
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Erklären Sie Retrieval Augmented Generation",
    "language": "de"
  }'
```

---

## See Also

- [Full API Reference](../api/README.md)
- [Python Examples](python_examples.md)
- [n8n Workflows](workflow_examples.md)

---

**[⬆ Back to Documentation](../README.md)**