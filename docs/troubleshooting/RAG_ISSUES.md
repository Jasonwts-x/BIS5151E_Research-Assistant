# RAG Troubleshooting

## Weaviate Connection Issues

### Symptom: "Collection does not exist"
**Cause**: Weaviate index not initialized

**Solution**:
```bash
# Reset and reinitialize
python -m src.rag.cli reset-index --yes
python -m src.rag.cli ingest-local
```

### Symptom: API ingestion fails but CLI works
**Causes**:
1. Network isolation between containers
2. Weaviate client connection error
3. File permission issues

**Solution**:
```bash
# 1. Check network connectivity
docker compose exec api ping weaviate
docker compose exec api curl http://weaviate:8080/v1/.well-known/ready

# 2. Check Weaviate health
curl http://localhost:8080/v1/.well-known/ready

# 3. Check API logs
docker compose logs api | grep -i error

# 4. Try ingestion with verbose logging
docker compose exec api python -m src.rag.cli ingest-local --pattern "*"
```

### Symptom: ArXiv ingestion timeouts
**Cause**: Slow PDF downloads or network issues

**Solution**:
```bash
# 1. Test external connectivity
docker compose exec api curl -I https://arxiv.org

# 2. Reduce max_results
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "max_results": 1}'

# 3. Use CLI instead (more stable)
docker compose exec api python -m src.rag.cli ingest-arxiv "test" --max-results 1
```

## Schema Mismatch Issues

### Symptom: "Schema mismatch detected"
**Cause**: Weaviate schema changed between versions

**Solution**:
```bash
# Option 1: Reset (loses data)
curl -X DELETE http://localhost:8000/rag/admin/reset-index

# Option 2: Enable auto-reset (dev only)
# Edit .env:
ALLOW_SCHEMA_RESET=true

# Then restart API
docker compose restart api
```

## Performance Issues

### Symptom: Slow retrieval
**Causes**:
1. Too many documents
2. Large chunk size
3. No index optimization

**Solutions**:
```bash
# 1. Reduce top_k
# Edit .env:
RAG_TOP_K=3  # Default is 5

# 2. Optimize chunk size
RAG_CHUNK_SIZE=200  # Smaller chunks = faster

# 3. Check document count
curl http://localhost:8000/rag/stats
```

## Data Quality Issues

### Symptom: Retrieved documents not relevant
**Solutions**:
1. Adjust hybrid search parameters
2. Re-ingest with better chunking
3. Add more documents for better coverage
```bash
# Check what's in the index
python -m src.rag.cli query "test" --top-k 10

# Re-ingest with better settings
# Edit .env:
RAG_CHUNK_SIZE=300
RAG_CHUNK_OVERLAP=50

# Reset and reingest
python -m src.rag.cli reset-index --yes
python -m src.rag.cli ingest-local
```