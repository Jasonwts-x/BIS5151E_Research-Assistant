# Contributing to ResearchAssistantGPT

Thank you for your interest in contributing! This guide will help you get started.

---

## 📜 Code of Conduct

Be respectful, inclusive, and constructive. We value:
- Respectful communication
- Constructive feedback
- Collaborative problem-solving
- Learning from mistakes

---

## 🚀 Getting Started

### 1. Fork & Clone
```bash
# Fork the repository on GitHub (click "Fork" button)

# Clone your fork
git clone https://github.com/YOUR_USERNAME/BIS5151E_Research-Assistant.git
cd BIS5151E_Research-Assistant

# Add upstream remote
git remote add upstream https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git
```

### 2. Set Up Development Environment

**Option A: DevContainer (Recommended)**
```bash
# Open in VS Code
code .

# VS Code will prompt: "Reopen in Container"
# Click it and wait for container to build (~2-3 minutes first time)
```

**Container includes**:
- Python 3.11
- All project dependencies
- Ruff, Black, MyPy
- pytest
- Git
- Access to all Docker services

**Option B: Local Python Environment**
```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Start Infrastructure Services
```bash
# Start Docker services
docker compose -f docker/docker-compose.yml up -d

# Verify services are healthy
python scripts/admin/health_check.py
```

---

## 🛠️ Development Workflow

### 1. Create a Branch
```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

**Branch naming conventions**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions
- `eval/` - Evaluation improvements

### 2. Make Changes

**Before committing, always run**:
```bash
# Auto-format code
black src tests

# Lint and fix issues
ruff check src tests --fix

# Type check
mypy src

# Run tests
pytest tests/ -v
```

**Testing requirements**:
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term

# Target: >80% coverage for new code
```

### 3. Commit Your Changes

We use [Conventional Commits](https://www.conventionalcommits.org/):
```bash
git add <files>
git commit -m "type(scope): description"
```

**Commit types**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code formatting (no logic change)
- `refactor:` - Code restructuring (no feature change)
- `test:` - Adding/updating tests
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

**Optional scope**: `agents`, `api`, `rag`, `eval`, `docker`, `docs`

**Examples**:
```bash
git commit -m "feat(agents): add translator agent for multilingual support"
git commit -m "fix(rag): resolve Weaviate connection timeout"
git commit -m "docs(api): add webhook integration examples"
git commit -m "test(rag): add unit tests for document processor"
git commit -m "refactor(eval): simplify guardrails validation logic"
```

### 4. Push and Create Pull Request
```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# Go to: https://github.com/YOUR_USERNAME/BIS5151E_Research-Assistant
# Click "Compare & pull request"
```

**Pull Request Guidelines**:
- Use descriptive title
- Reference related issue: "Fixes #123"
- Describe changes made
- Include test results
- Add screenshots (if UI changes)

---

## 🎨 Coding Standards

### Python Style

**Follow PEP 8** enforced by ruff and black:
```python
# Good: Type hints, docstrings, clear naming
def fetch_papers(query: str, max_results: int = 10) -> list[Document]:
    """
    Fetch papers from ArXiv.
    
    Args:
        query: Search query string
        max_results: Maximum number of papers to fetch
        
    Returns:
        List of Document objects
    """
    ...

# Bad: No types, unclear naming, no docs
def fetch(q, n=10):
    ...
```

### Naming Conventions
```python
# Variables: snake_case
user_query = "What is AI?"
max_results = 10

# Functions: snake_case
def process_query(query: str) -> dict:
    ...

# Classes: PascalCase
class RAGPipeline:
    ...

# Constants: UPPER_SNAKE_CASE
MAX_CHUNK_SIZE = 500
DEFAULT_MODEL = "qwen3:1.7b"

# Private methods/variables: leading underscore
def _normalize_metadata(self, doc: Document) -> None:
    ...
```

### Import Organization
```python
# Standard library
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Dict, List

# Third-party
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Local
from src.rag.core.pipeline import RAGPipeline
from src.utils.config import load_config
```

### Logging

Use structured logging:
```python
import logging

logger = logging.getLogger(__name__)

# Good
logger.info(
    "Processing document",
    extra={"file": file_path, "chunks": len(chunks)}
)

# Bad
print(f"Processing {file_path}")  # Never use print
```

### Error Handling

Be specific with exceptions:
```python
# Good
try:
    result = api.call()
except ConnectionError as e:
    logger.error("API connection failed: %s", e)
    raise HTTPException(status_code=503, detail="Service unavailable")
except TimeoutError as e:
    logger.warning("API timeout, retrying: %s", e)
    # Retry logic
except ValueError as e:
    logger.error("Invalid input: %s", e)
    raise HTTPException(status_code=400, detail=str(e))
    
# Bad
try:
    result = api.call()
except Exception:
    pass  # Silent failure - NEVER DO THIS
```

### Docstrings

Use Google-style docstrings:
```python
def chunk_document(
    text: str,
    chunk_size: int = 350,
    overlap: int = 50
) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Target size of each chunk in characters
        overlap: Number of overlapping characters between chunks
        
    Returns:
        List of text chunks
        
    Raises:
        ValueError: If chunk_size <= overlap
        
    Example:
        >>> chunks = chunk_document("Long text...", chunk_size=500, overlap=50)
        >>> len(chunks)
        15
    """
    ...
```

---

## 🧪 Testing Guidelines

### Test Organization
```
tests/
├── unit/               # Fast, isolated tests (no external services)
│   ├── test_agents/
│   ├── test_api/
│   ├── test_eval/
│   └── test_rag/
├── integration/        # Slow, requires Docker services
│   └── test_rag_ingestion_e2e.py
├── fixtures/           # Shared test data
└── conftest.py         # Pytest configuration
```

### Writing Tests
```python
import pytest
from src.rag.core.processor import DocumentProcessor

def test_chunk_id_deterministic():
    """Chunk IDs should be deterministic based on content."""
    processor = DocumentProcessor()
    
    # Same content should produce same ID
    chunk1 = "This is a test chunk."
    chunk2 = "This is a test chunk."
    
    id1 = processor._generate_chunk_id(chunk1, "doc1", 0)
    id2 = processor._generate_chunk_id(chunk2, "doc1", 0)
    
    assert id1 == id2
    
def test_chunk_id_unique():
    """Different content should produce different IDs."""
    processor = DocumentProcessor()
    
    id1 = processor._generate_chunk_id("Content A", "doc1", 0)
    id2 = processor._generate_chunk_id("Content B", "doc1", 0)
    
    assert id1 != id2
```

### Running Tests
```bash
# All tests
pytest tests/ -v

# Specific category
pytest tests/unit/ -v
pytest tests/integration/ -v

# Specific file
pytest tests/unit/test_rag/test_processor.py -v

# Specific test
pytest tests/unit/test_rag/test_processor.py::test_chunk_id_deterministic -v

# With coverage
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html

# Skip slow tests
pytest tests/unit/ -v  # Only fast tests
```

---

## 📝 Documentation Guidelines

### Code Documentation

- Every public function/class needs a docstring
- Complex logic needs inline comments
- Use type hints everywhere

### Updating Documentation

When adding features:

1. **Update relevant docs** in `docs/`
2. **Add examples** to `docs/examples/`
3. **Update API docs** if new endpoints
4. **Update CHANGELOG.md**

### Documentation Files to Update

| Change Type | Update These Files |
|-------------|-------------------|
| New feature | README.md, CHANGELOG.md, relevant docs/ file |
| API endpoint | docs/api/README.md, CHANGELOG.md |
| Configuration | docs/setup/INSTALLATION.md, .env.example |
| Bug fix | CHANGELOG.md |
| Breaking change | CHANGELOG.md (with migration notes), README.md |

---

## 🚀 Release Process

For maintainers:

### 1. Version Bump

Update version in:
- `CHANGELOG.md` - Add new version section
- `src/api/routers/system.py` - Update VERSION constant

### 2. Create Release
```bash
# Tag release
git tag -a v1.0.0 -m "Release v1.0.0: First stable release"
git push origin v1.0.0

# GitHub Actions will create release automatically
```

### 3. Post-Release

- Announce in discussions
- Update documentation
- Close related issues

---

## 🐛 Reporting Bugs

Use [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues/new) with bug template.

**Include**:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- System info (OS, Docker version)
- Logs (if relevant)
- Screenshots (if UI issue)

---

## 💡 Suggesting Features

Use [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues/new) with feature template.

**Include**:
- Use case (why is this needed?)
- Proposed solution
- Alternatives considered
- Willing to implement? (yes/no)

---

## ❓ Questions

- **General**: [GitHub Discussions](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/discussions)
- **Bugs**: [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues)
- **Security**: Email team privately (see README)

---

## 📄 License

By contributing, you agree your contributions will be licensed under the same Academic Use License as the project. See [LICENSE](LICENSE).

---

## 🙏 Recognition

Contributors will be:
- Listed in project credits
- Mentioned in release notes
- Added to CONTRIBUTORS.md (if significant contribution)

---

**Thank you for contributing! 🎉**

**Questions?** Open a discussion or ask in your pull request.