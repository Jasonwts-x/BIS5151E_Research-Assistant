# CLI Examples

Command-line interface examples for ResearchAssistantGPT.

---

## 📋 Available CLI Tools

| Script | Purpose | Location |
|--------|---------|----------|
| `ingest_arxiv.py` | Ingest papers from ArXiv | `scripts/cli/` |
| `query_rag.py` | Query documents | `scripts/cli/` |
| `health_check.py` | Health monitoring | `scripts/admin/` |
| `backup.sh` | Backup data | `scripts/admin/` |

---

## 🚀 Basic Usage

### Health Check
```bash
# Check all services
python scripts/admin/health_check.py

# Expected output:
# ✅ API Service (http://localhost:8000) - healthy
# ✅ Weaviate - ready
# ✅ Ollama - running
```

---

### Ingest Papers from ArXiv
```bash
# Ingest 3 papers on machine learning
python scripts/cli/ingest_arxiv.py \
    --query "machine learning" \
    --max-results 3

# With custom API URL
python scripts/cli/ingest_arxiv.py \
    --query "neural networks" \
    --max-results 5 \
    --api-url http://localhost:8000
```

**Options**:
```
--query TEXT          ArXiv search query [required]
--max-results INT     Max papers to fetch [default: 10]
--api-url TEXT        API base URL [default: http://localhost:8000]
```

---

### Query Documents
```bash
# Simple query
python scripts/cli/query_rag.py \
    --query "What are neural networks?"

# With language preference
python scripts/cli/query_rag.py \
    --query "Was ist maschinelles Lernen?" \
    --language de

# With more context
python scripts/cli/query_rag.py \
    --query "Explain transformers" \
    --top-k 10
```

**Options**:
```
--query TEXT          Research question [required]
--language TEXT       Response language [default: en]
--top-k INT          Context chunks [default: 5]
--api-url TEXT       API base URL [default: http://localhost:8000]
```

---

## 🔄 Batch Processing

### Ingest Multiple Topics
```bash
#!/bin/bash
# ingest_multiple.sh

topics=("machine learning" "deep learning" "neural networks")

for topic in "${topics[@]}"; do
    echo "Ingesting: $topic"
    python scripts/cli/ingest_arxiv.py --query "$topic" --max-results 3
    sleep 5  # Rate limiting
done

echo "✅ All topics ingested"
```

**Run**:
```bash
chmod +x ingest_multiple.sh
./ingest_multiple.sh
```

---

### Query Multiple Questions
```bash
#!/bin/bash
# query_multiple.sh

questions=(
    "What is machine learning?"
    "What are neural networks?"
    "Explain deep learning"
)

for question in "${questions[@]}"; do
    echo ""
    echo "Q: $question"
    python scripts/cli/query_rag.py --query "$question"
done
```

---

## 📊 Automation Examples

### Daily ArXiv Digest (Cron)
```bash
# Add to crontab: crontab -e
0 9 * * * /path/to/scripts/daily_digest.sh >> /var/log/research_digest.log 2>&1
```

**daily_digest.sh**:
```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
TOPIC="machine learning"

# Ingest latest papers
python scripts/cli/ingest_arxiv.py --query "$TOPIC" --max-results 5

# Generate summary
python scripts/cli/query_rag.py \
    --query "Summarize recent developments in $TOPIC" \
    > /tmp/digest_$DATE.txt

# Email results (optional)
mail -s "ArXiv Digest: $DATE" user@example.com < /tmp/digest_$DATE.txt
```

---

### Scheduled Health Monitoring
```bash
# crontab -e
*/15 * * * * /path/to/scripts/monitor.sh
```

**monitor.sh**:
```bash
#!/bin/bash
LOG_FILE="/var/log/health_checks.log"

echo "=== $(date) ===" >> $LOG_FILE
python scripts/admin/health_check.py >> $LOG_FILE 2>&1

# Alert if unhealthy
if [ $? -ne 0 ]; then
    echo "❌ Health check failed!" | mail -s "Research Assistant Alert" admin@example.com
fi
```

---

## 🛠️ Development Tools

### Test Ingestion Pipeline
```bash
# Test with single paper
python scripts/cli/ingest_arxiv.py \
    --query "test query" \
    --max-results 1

# Verify
curl http://localhost:8000/rag/stats | jq
```

---

### Benchmark Query Performance
```bash
#!/bin/bash
# benchmark.sh

QUERIES=(
    "What is AI?"
    "Explain neural networks"
    "Deep learning applications"
)

for query in "${QUERIES[@]}"; do
    echo "Testing: $query"
    time python scripts/cli/query_rag.py --query "$query" > /dev/null
done
```

---

## 📚 Related Documentation

- **[Python Examples](PYTHON_EXAMPLES.md)** - API integration
- **[Basic Usage](BASIC_USAGE.md)** - curl/PowerShell examples
- **[Command Reference](../guides/COMMAND_REFERENCE.md)** - All commands

---

**[⬅ Back to Examples](README.md)**