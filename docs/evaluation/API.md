# Evaluation API Reference

Complete API reference for the evaluation service.

---

## Base URL
```
http://localhost:8502
```

---

## Authentication

Currently no authentication required (development only).

For production, add API key authentication.

---

## Endpoints

### Health Checks

#### GET /health

Check if service is alive.

**Response:**
```json
{
  "status": "healthy",
  "service": "evaluation"
}
```

---

#### GET /health/ready

Check if service is ready (includes database check).

**Response:**
```json
{
  "status": "ready",
  "database": "connected",
  "trulens": "initialized"
}
```

**Errors:**
- `503 Service Unavailable` - Database not available

---

### Evaluation

#### POST /metrics/evaluate

Evaluate a query/answer pair with full metrics.

**Request Body:**
```json
{
  "query": "What is machine learning?",
  "answer": "Machine learning is a subset of AI...",
  "context": "Retrieved context here...",
  "language": "en",
  "metadata": {
    "user_id": "123",
    "session_id": "abc"
  }
}
```

**Response:**
```json
{
  "record_id": "abc123",
  "timestamp": "2026-01-26T10:30:00",
  "query": "What is machine learning?",
  "answer_length": 150,
  "summary": {
    "passed": true,
    "overall_score": 0.82,
    "issues": [],
    "warnings": []
  },
  "trulens": {
    "overall_score": 0.82,
    "trulens": {
      "groundedness": 0.85,
      "answer_relevance": 0.80,
      "context_relevance": 0.81
    }
  },
  "guardrails": {
    "input_passed": true,
    "output_passed": true,
    "overall_passed": true,
    "violations": [],
    "warnings": []
  },
  "performance": {
    "total_time": 2.5
  }
}
```

---

#### GET /metrics/leaderboard

Get evaluation leaderboard sorted by score.

**Query Parameters:**
- `limit` (int, default=100): Maximum records to return
- `app_id` (string, optional): Filter by application ID

**Response:**
```json
{
  "total_records": 45,
  "entries": [
    {
      "record_id": "abc123",
      "timestamp": "2026-01-26T10:30:00",
      "query": "What is machine learning?",
      "overall_score": 0.85,
      "groundedness": 0.88,
      "answer_relevance": 0.82,
      "context_relevance": 0.85,
      "total_time": 2.5,
      "passed_guardrails": true
    }
  ]
}
```

---

#### GET /metrics/record/{record_id}

Get detailed evaluation record by ID.

**Path Parameters:**
- `record_id` (string): Evaluation record ID

**Response:**
Same format as `/metrics/evaluate` response.

**Errors:**
- `404 Not Found` - Record doesn't exist

---

### Benchmarking (Optional)

#### POST /metrics/benchmark/consistency

Run consistency benchmark (multiple runs of same query).

**Request Body:**
```json
{
  "query": "What is AI?",
  "context": "Context here...",
  "runs": 3
}
```

**Response:**
```json
{
  "consistent": true,
  "std_dev": 0.08,
  "mean": 0.82,
  "min": 0.78,
  "max": 0.86,
  "runs": 3,
  "threshold": 0.15
}
```

---

#### POST /metrics/benchmark/paraphrase

Run paraphrase stability benchmark.

**Request Body:**
```json
{
  "query_variations": [
    "What is AI?",
    "Can you explain artificial intelligence?",
    "Define AI"
  ],
  "context": "Context here...",
  "answer": "Answer here..."
}
```

**Response:**
```json
{
  "stable": true,
  "max_diff": 0.12,
  "min_score": 0.75,
  "max_score": 0.87,
  "mean_score": 0.81,
  "scores": [0.80, 0.75, 0.87],
  "variations": 3,
  "threshold": 0.20
}
```

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request: missing required field 'query'"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Evaluation failed: database connection error"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Database not available"
}
```

---

## Rate Limiting

Currently no rate limiting (development only).

For production, implement rate limiting:
- 100 requests per minute per IP
- 1000 requests per hour per API key

---

## Caching

Evaluation results are cached to avoid recomputation:

- **In-Memory Cache**: Single instance (default)
- **Redis Cache**: Multi-instance deployments

Set `REDIS_URL` environment variable to enable Redis caching.

Cache TTL: 1 hour (configurable)

---

## Examples

### Python
```python
import requests

# Evaluate
response = requests.post(
    "http://localhost:8502/metrics/evaluate",
    json={
        "query": "What is ML?",
        "answer": "Machine learning...",
        "context": "Context...",
    }
)

result = response.json()
print(f"Score: {result['summary']['overall_score']}")

# Get leaderboard
response = requests.get("http://localhost:8502/metrics/leaderboard?limit=10")
leaderboard = response.json()

for entry in leaderboard['entries']:
    print(f"{entry['query']}: {entry['overall_score']}")
```

### PowerShell
```powershell
# Evaluate
$body = @{
    query = "What is ML?"
    answer = "Machine learning..."
    context = "Context..."
} | ConvertTo-Json

$result = Invoke-RestMethod `
    -Uri "http://localhost:8502/metrics/evaluate" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$result.summary.overall_score

# Get leaderboard
$leaderboard = Invoke-RestMethod `
    -Uri "http://localhost:8502/metrics/leaderboard?limit=10"

$leaderboard.entries
```

### cURL
```bash
# Evaluate
curl -X POST "http://localhost:8502/metrics/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is ML?",
    "answer": "Machine learning...",
    "context": "Context..."
  }'

# Get leaderboard
curl "http://localhost:8502/metrics/leaderboard?limit=10"
```

---

## OpenAPI/Swagger

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8502/docs
- **ReDoc**: http://localhost:8502/redoc
- **OpenAPI JSON**: http://localhost:8502/openapi.json