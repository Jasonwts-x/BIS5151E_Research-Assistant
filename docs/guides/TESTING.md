# Testing Guide

How to run tests for ResearchAssistantGPT.

---

## Test Structure
```
tests/
├── unit/           # Unit tests (fast, isolated)
│   ├── agents/     # Agent logic tests
│   ├── api/        # API schema tests
│   ├── eval/       # Evaluation module tests
│   └── rag/        # RAG pipeline tests
├── integration/    # Integration tests (slower, require services)
└── e2e/            # End-to-end tests (full workflow)
```

---

## Running Tests

### All Tests
```powershell
pytest
```

### Specific Module
```powershell
pytest tests/unit/agents/
pytest tests/unit/eval/
```

### With Coverage
```powershell
pytest --cov=src --cov-report=html
```

### Verbose Output
```powershell
pytest -v
```

### Stop on First Failure
```powershell
pytest -x
```

---

## Test Configuration

**File:** `pytest.ini`
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -ra
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

---

## Writing Tests

### Unit Test Example
```python
def test_function_name():
    """Test description."""
    # Arrange
    input_data = "test"
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
```

### Integration Test Example
```python
@pytest.mark.integration
def test_api_endpoint():
    """Test API integration."""
    response = client.post("/endpoint", json={...})
    assert response.status_code == 200
```

---

## CI/CD

Tests run automatically on:
- Every push to main
- Every pull request

See `.github/workflows/ci.yml`