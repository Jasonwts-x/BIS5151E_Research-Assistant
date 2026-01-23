# Testing Guide

## Prerequisites

1. **Services Running**:
```bash
   docker compose -f docker/docker-compose.yml up -d
   ./scripts/admin/health_check.py  # Verify all healthy
```

2. **Test Data**:
```bash
   # Ingest sample documents
   docker compose exec api python -m src.rag.cli ingest-local
```

## Running Tests

### Quick Test (All)
```bash
# From project root
pytest tests/ -v

# Or from devcontainer
docker compose exec devcontainer pytest tests/ -v
```

### By Category

**Unit Tests Only** (fast, no external services):
```bash
pytest tests/unit/ -v
```

**Integration Tests Only** (slow, requires services):
```bash
pytest tests/integration/ -v
```

**Specific Module**:
```bash
pytest tests/unit/test_rag/ -v
pytest tests/integration/test_rag_ingestion_e2e.py -v
```

### With Coverage
```bash
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Skip Slow Tests
```bash
# Skip integration tests
pytest tests/unit/ -v

# Or set environment variable
export SKIP_INTEGRATION_TESTS=1
pytest tests/ -v
```

## Test Organization
```
tests/
├── unit/               # Fast, isolated tests
│   ├── test_rag/
│   ├── test_agents/
│   └── test_api/
├── integration/        # Slow, requires services
└── fixtures/           # Shared test data
```

## Debugging Failed Tests

### View Full Output
```bash
pytest tests/ -v -s  # -s shows print statements
```

### Run Single Test
```bash
pytest tests/unit/test_rag/test_processor.py::test_chunk_id_deterministic -v
```

### Debug Mode
```bash
pytest tests/ --pdb  # Drop into debugger on failure
```

## Common Issues

### Issue: "Collection does not exist"
**Solution**:
```bash
docker compose exec api python -m src.rag.cli reset-index --yes
docker compose exec api python -m src.rag.cli ingest-local
```

### Issue: "Connection refused"
**Solution**:
```bash
# Check services are running
docker compose ps
./scripts/admin/health_check.py
```

### Issue: Import errors
**Solution**:
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/workspaces/BIS5151E_Research-Assistant
# Or run from devcontainer where it's set automatically
```

## CI/CD Testing

Tests run automatically on:
- Push to `main`
- Pull requests

See `.github/workflows/ci.yml` for configuration.