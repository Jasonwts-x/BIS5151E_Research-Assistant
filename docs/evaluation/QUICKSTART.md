# Evaluation Quick Start

Get started with the evaluation system in 5 minutes.

---

## 1. Start Services
```bash
# Start all services including evaluation
docker compose up -d

# Wait for health checks
docker compose ps
```

---

## 2. Access Dashboard

Open browser: **http://localhost:8501**

You should see the evaluation dashboard with:
- Overview page (currently empty)
- Performance metrics
- Quality metrics

---

## 3. Run a Query
```bash
# Run a test query
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "What is retrieval augmented generation?",
    "language": "en"
  }'
```

---

## 4. View Evaluation Results

The response includes evaluation metrics:
```json
{
  "topic": "What is retrieval augmented generation?",
  "answer": "...",
  "evaluation": {
    "trulens": {
      "groundedness": 0.75,
      "answer_relevance": 0.82
    },
    "guardrails": {
      "input_passed": true,
      "output_passed": true
    },
    "performance": {
      "total_time": 42.3,
      "rag_retrieval": 2.1,
      "crew_execution": 39.8
    }
  }
}
```

---

## 5. Check Dashboard

Refresh the dashboard at http://localhost:8501 to see your evaluation results visualized.

---

## Troubleshooting

**Dashboard shows "No data":**
- Run at least one query first
- Check eval service is running: `docker compose ps eval`

**Evaluation service not starting:**
- Check logs: `docker compose logs eval`
- Verify PostgreSQL is running: `docker compose ps postgres`

---

## Next Steps

- Review [Full Documentation](README.md)
- Configure guardrails: `docker/env`
- Set up alerts for low quality scores