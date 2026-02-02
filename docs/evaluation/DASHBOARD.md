# Evaluation Dashboard

Web-based dashboard for monitoring RAG quality metrics.

---

## ⚠️ Current Status

**Status**: Experimental / Stub Implementation

The evaluation dashboard is currently in early development. This document describes:
- What's implemented (basic logging)
- What's planned (web dashboard)
- How to enable it
- Future features

---

## 📊 Current Implementation

### What's Available Now

**Logging-Based Metrics**:
- Metrics are logged to console during query processing
- Can be viewed via `docker compose logs api`
- No persistent storage (except PostgreSQL schema)
- No visualization

**Example Log Output**:
```
INFO - Query: "What are neural networks?"
INFO - Guardrails input validation: PASSED
INFO - Context retrieval: 0.52s
INFO - Writer agent: 10.3s
INFO - Reviewer agent: 5.1s
INFO - FactChecker agent: 10.2s
INFO - TruLens metrics: answer_relevance=0.89, context_relevance=0.82, groundedness=0.94
INFO - Total processing time: 28.4s
```

**View Logs**:
```bash
# All logs
docker compose logs api -f

# Filtered for metrics
docker compose logs api | grep -E "metric|score|validation"
```

---

## 🎯 Planned Features

### TruLens Dashboard (v1.1.0)

**Overview**: Web-based dashboard showing real-time quality metrics

**URL**: http://localhost:8502 (Streamlit app)

**Features**:
- 📊 Real-time metric visualization
- 📈 Historical trends (7/30/90 days)
- 🔍 Query-level drill-down
- 📉 Performance graphs
- 🎯 Quality score distribution

**Screenshot** (mockup):
```
┌─────────────────────────────────────────────────────────┐
│ ResearchAssistantGPT - Evaluation Dashboard             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📊 Overall Metrics (Last 24h)                          │
│  ┌──────────────┬──────────────┬──────────────┐         │
│  │Answer Rel.   │Context Rel.  │Groundedness  │         │
│  │   0.87       │    0.81      │    0.92      │         │
│  └──────────────┴──────────────┴──────────────┘         │
│                                                         │
│  📈 Trend (Last 7 days)                                 │
│  │                                  ╱───╲               │
│  │                           ╱────╱      ╲              │
│  │                    ╱────╱               ╲────        │
│  │             ╱────╱                           ╲       │
│  └─────────────────────────────────────────────────     │
│    Mon  Tue  Wed  Thu  Fri  Sat  Sun                    │
│                                                         │
│  📋 Recent Queries                                      │
│  ┌────────────────────────────────────────────────┐     │
│  │ Query                        │ Rel. │ Ground.  │     │
│  ├────────────────────────────────────────────────┤     │
│  │ What are neural networks?    │ 0.92 │ 0.95     │     │
│  │ Explain transformers         │ 0.88 │ 0.91     │     │
│  │ Deep learning applications   │ 0.85 │ 0.89     │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Enabling the Dashboard (Future)

### Step 1: Enable TruLens
```bash
# Edit .env
EVAL_ENABLE_TRULENS=true
EVAL_ENABLE_PERFORMANCE=true
```

### Step 2: Start Dashboard Service

**Option A: Docker Compose** (recommended):
```yaml
# docker-compose.yml (future)
services:
  eval-dashboard:
    build:
      context: .
      dockerfile: .devcontainer/Dockerfile
      target: eval
    container_name: eval-dashboard
    command: streamlit run src/eval/dashboard/app.py --server.port 8502
    ports:
      - "8502:8502"
    networks:
      - research_net
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://research_assistant:${POSTGRES_PASSWORD}@postgres:5432/trulens
```
```bash
# Start with dashboard
docker compose up -d eval-dashboard
```

**Option B: Local** (development):
```bash
# Install Streamlit
pip install streamlit plotly

# Run dashboard
streamlit run src/eval/dashboard/app.py
```

### Step 3: Access Dashboard

Open: http://localhost:8502

---

## 📊 Dashboard Features

### 1. Overview Tab

**Metrics Cards**:
- Answer Relevance (current avg)
- Context Relevance (current avg)
- Groundedness (current avg)
- Total Queries (count)
- Avg Response Time (seconds)

**Time Range Selector**:
- Last 24 hours
- Last 7 days
- Last 30 days
- Custom range

---

### 2. Trends Tab

**Line Charts**:
- Quality metrics over time
- Response time trends
- Query volume

**Filters**:
- Date range
- Language (en/de/fr/es)
- Query type

---

### 3. Query Analysis Tab

**Query List**:
- Recent queries
- Quality scores per query
- Processing time
- Click to view details

**Query Detail View**:
- Full query text
- Generated answer
- Retrieved context
- All metrics (relevance, groundedness, etc.)
- Agent timing breakdown

---

### 4. Performance Tab

**Charts**:
- Response time distribution (histogram)
- Latency by component (stacked bar)
- Throughput (queries/hour)

**Resource Usage** (future):
- CPU usage
- Memory usage
- GPU usage (if enabled)

---

### 5. Leaderboard Tab

**Best Performing Queries**:
- Highest quality scores
- Fastest responses
- Most cited sources

**Worst Performing Queries**:
- Lowest quality scores
- Slowest responses
- Flagged by Guardrails

---

## 🗄️ Data Storage

### PostgreSQL Schema

**Database**: `trulens`

**Tables**:
- `trulens_records` - Main metrics
- `quality_metrics` - Detailed quality scores
- `guardrails_results` - Validation results

See [Database Schema](../architecture/DATABASE.md) for details.

### Data Retention

**Default**: Indefinite

**Cleanup** (manual):
```sql
-- Delete records older than 90 days
DELETE FROM trulens_records
WHERE timestamp < NOW() - INTERVAL '90 days';
```

**Future**: Automatic retention policies

---

## 📈 Metrics Displayed

### Real-Time Metrics

Updated live as queries are processed:
- Current query count
- Avg response time (last 100 queries)
- Live quality scores

### Historical Metrics

Aggregated from database:
- Daily averages
- Weekly trends
- Monthly comparisons

### Metric Details

| Metric | Description | Display |
|--------|-------------|---------|
| **Answer Relevance** | Query-answer relevance | Line chart, avg card |
| **Context Relevance** | Context quality | Line chart, avg card |
| **Groundedness** | Claim support | Line chart, avg card |
| **Response Time** | Total latency | Histogram, trend line |
| **Citation Coverage** | % with citations | Percentage gauge |
| **Query Volume** | Queries/hour | Bar chart |

---

## 🔧 Configuration

### Environment Variables
```bash
# Dashboard settings (future)
DASHBOARD_ENABLED=true
DASHBOARD_PORT=8502
DASHBOARD_REFRESH_INTERVAL=5  # seconds
DASHBOARD_RETENTION_DAYS=90

# Metrics to display
DASHBOARD_SHOW_TRULENS=true
DASHBOARD_SHOW_GUARDRAILS=true
DASHBOARD_SHOW_PERFORMANCE=true
```

### Custom Metrics

Add custom metrics to dashboard:
```python
# src/eval/dashboard/metrics.py
def custom_metric(query, answer, context):
    # Calculate custom metric
    score = ...
    return score

# Register in dashboard
dashboard.add_metric("Custom Metric", custom_metric)
```

---

## 📊 Export Features (Future)

### Export to CSV
```python
# From dashboard UI
# Click "Export" → Select date range → Download CSV

# Or via API
curl http://localhost:8502/api/export?start=2025-01-01&end=2025-02-01 > metrics.csv
```

**CSV Format**:
```csv
timestamp,query,answer_relevance,context_relevance,groundedness,response_time
2025-02-02T10:30:00,What are neural networks?,0.89,0.82,0.94,28.4
2025-02-02T10:35:00,Explain transformers,0.91,0.85,0.92,26.7
```

### Export to PDF

Generate PDF reports:
- Summary statistics
- Trend charts
- Best/worst queries
- Custom date range

---

## 🔍 Monitoring Alerts (Future)

### Alert Rules

Configure alerts for quality drops:
```yaml
# alerts.yaml
alerts:
  - name: "Low Answer Relevance"
    metric: answer_relevance
    threshold: 0.7
    condition: below
    action: email
    
  - name: "Slow Response"
    metric: response_time
    threshold: 40
    condition: above
    action: slack
```

### Alert Channels

- Email notifications
- Slack/Discord webhooks
- In-dashboard notifications

---

## 🐛 Troubleshooting

### Issue: Dashboard not starting

**Solution**:
```bash
# Check if Streamlit is installed
pip install streamlit

# Check PostgreSQL connection
psql -h localhost -U research_assistant -d trulens

# Check logs
docker compose logs eval-dashboard
```

### Issue: No data showing

**Solution**:
```bash
# Verify TruLens is enabled
echo $EVAL_ENABLE_TRULENS  # Should be "true"

# Check database has data
psql -h localhost -U research_assistant -d trulens -c "SELECT COUNT(*) FROM trulens_records;"

# Run a test query to generate data
curl -X POST http://localhost:8000/research/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test query","language":"en"}'
```

### Issue: Dashboard slow/unresponsive

**Solution**:
```bash
# Reduce retention window
# Edit dashboard config
DASHBOARD_RETENTION_DAYS=30  # Instead of 90

# Or clear old data
DELETE FROM trulens_records WHERE timestamp < NOW() - INTERVAL '30 days';
```

---

## 🔮 Future Enhancements

### v1.1.0 (Q2 2025)
- [ ] Basic Streamlit dashboard
- [ ] TruLens integration
- [ ] PostgreSQL storage
- [ ] Real-time metrics

### v1.2.0 (Q3 2025)
- [ ] Advanced filtering
- [ ] Custom date ranges
- [ ] Export to CSV/PDF
- [ ] Email alerts

### v2.0.0 (Q4 2025)
- [ ] Multi-user support
- [ ] Role-based access
- [ ] API for metrics
- [ ] Grafana integration
- [ ] Prometheus exporters

---

## 📚 Related Documentation

- **[Evaluation Overview](README.md)** - Introduction
- **[Metrics Explained](METRICS.md)** - What metrics mean
- **[TruLens Setup](TRULENS.md)** - Enable TruLens
- **[Database Schema](../architecture/DATABASE.md)** - Data structure

---

**[⬅ Back to Evaluation](README.md)**