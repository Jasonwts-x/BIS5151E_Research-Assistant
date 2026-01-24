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
# Fork the repository on GitHub
# Then clone your fork
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
# Click it and wait for container to build
```

**Option B: Local Setup**
```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Start Services
```bash
# Start infrastructure
docker compose -f docker/docker-compose.yml up -d

# Verify services
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

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions

### 2. Make Changes

**Follow our coding standards:**
```bash
# Before committing, always run:
ruff check src tests --fix
black src tests
mypy src
```

**Testing requirements:**
```bash
# Run tests
pytest tests/ -v

# Ensure coverage doesn't drop
pytest tests/ --cov=src --cov-report=term

# Target: >80% coverage for new code
```

### 3. Commit Your Changes

We use [Conventional Commits](https://www.conventionalcommits.org/):
```bash
git add .
git commit -m "type: description"
```

**Commit types:**
- `feat(folder):`       - New feature
- `fix(folder):`        - Bug fix
- `docs(folder):`       - Documentation only
- `style(folder):`      - Formatting, missing semicolons, etc.
- `refactor(folder):`   - Code change that neither fixes nor adds a feature
- `test(folder):`       - Adding tests
- `chore(folder):`      - Maintenance tasks

**Examples:**
```bash
git commit -m "feat: add multilingual support for German"
git commit -m "fix: resolve Weaviate connection timeout"
git commit -m "docs: update API endpoint examples"
git commit -m "test: add unit tests for RAG pipeline"
```

### 4. Push & Create Pull Request
```bash
# Push to your fork
git push origin feature/your-feature-name

# Then create PR on GitHub
```

---

## 📝 Pull Request Guidelines

### Before Submitting

Checklist:
- [ ] Code follows style guide (ruff + black)
- [ ] All tests pass (`pytest tests/`)
- [ ] Added tests for new features
- [ ] Updated documentation
- [ ] No merge conflicts with `main`
- [ ] Commit messages follow conventional format

### PR Description Template
```markdown
## Description
Brief description of changes.

## Related Issue
Fixes #123

## Changes Made
- Added feature X
- Modified component Y
- Removed deprecated Z

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manually tested

## Screenshots (if applicable)
[Add screenshots]

## Checklist
- [ ] Code formatted (black + ruff)
- [ ] Tests pass
- [ ] Documentation updated
```

### Review Process

1. **Automated checks** run (CI pipeline)
2. **Maintainer review** (1-2 days)
3. **Address feedback** (make changes)
4. **Approval & merge** (by maintainer)

---

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/           # Fast, isolated tests (no external services)
├── integration/    # Slow tests (require Docker services)
└── fixtures/       # Shared test data
```

### Writing Tests

**Unit test example:**
```python
# tests/unit/test_rag/test_processor.py
import pytest
from src.rag.ingestion.processor import DocumentProcessor

def test_chunk_text():
    processor = DocumentProcessor()
    text = "This is a test. " * 100
    chunks = processor.chunk_text(text, chunk_size=200)
    
    assert len(chunks) > 0
    assert all(len(c) <= 200 for c in chunks)
```

**Integration test example:**
```python
# tests/integration/test_rag_ingestion.py
import pytest
from src.rag.core import RAGPipeline

@pytest.mark.integration
def test_ingest_and_query(weaviate_client):
    pipeline = RAGPipeline.from_existing()
    
    # Test ingestion
    result = pipeline.ingest_local("data/raw/*.pdf")
    assert result.chunks_ingested > 0
    
    # Test retrieval
    docs = pipeline.run("test query", top_k=5)
    assert len(docs) > 0
```

### Running Tests
```bash
# All tests
pytest tests/ -v

# Unit only (fast)
pytest tests/unit/ -v

# Integration only (slow)
pytest tests/integration/ -v

# Specific test
pytest tests/unit/test_rag/test_processor.py::test_chunk_text -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 📚 Documentation Guidelines

### Code Documentation
```python
def process_document(file_path: str, chunk_size: int = 500) -> list[str]:
    """
    Process a document into chunks.
    
    Args:
        file_path: Path to document file (PDF or TXT)
        chunk_size: Maximum characters per chunk (default: 500)
    
    Returns:
        List of text chunks
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If chunk_size < 100
    
    Example:
        >>> chunks = process_document("paper.pdf", chunk_size=500)
        >>> len(chunks)
        42
    """
    ...
```

### README Updates

When adding features:
1. Update main [README.md](README.md) (if major feature)
2. Add detailed docs to [docs/](docs/)
3. Add examples to [docs/examples/](docs/examples/)
4. Update [CHANGELOG.md](CHANGELOG.md)

---

## 🎨 Coding Standards

### Python Style

**Follow PEP 8** enforced by ruff and black:
```bash
# Auto-format
black src tests

# Lint
ruff check src tests --fix

# Type check
mypy src
```

### Type Hints

Always use type hints:
```python
# Good
def fetch_papers(query: str, max_results: int = 10) -> list[Document]:
    ...

# Bad
def fetch_papers(query, max_results=10):
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
DEFAULT_MODEL = "qwen2.5:3b"
```

### Logging

Use structured logging:
```python
import logging

logger = logging.getLogger(__name__)

# Good
logger.info("Processing document", extra={"file": file_path, "chunks": len(chunks)})

# Bad
print(f"Processing {file_path}")
```

### Error Handling

Be specific:
```python
# Good
try:
    result = api.call()
except ConnectionError as e:
    logger.error("API connection failed: %s", e)
    raise
except TimeoutError as e:
    logger.warning("API timeout, retrying: %s", e)
    # Retry logic
    
# Bad
try:
    result = api.call()
except Exception:
    pass  # Silent failure
```

---

## 🚀 Release Process

For maintainers:

1. **Update version** in relevant files
2. **Update CHANGELOG.md**
3. **Create git tag**:
```bash
   git tag -a v0.4.0 -m "Release v0.4.0"
   git push origin v0.4.0
```
4. **GitHub Actions** will create release automatically

---

## 🐛 Reporting Bugs

Use [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues/new?template=bug_report.md).

**Include:**
- Expected behavior
- Actual behavior
- Steps to reproduce
- System info (OS, Docker version, etc.)
- Logs (if relevant)

---

## 💡 Suggesting Features

Use [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues/new?template=feature_request.md).

**Include:**
- Use case
- Proposed solution
- Alternatives considered

---

## ❓ Questions

- **General:** [GitHub Discussions](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/discussions)
- **Bugs:** [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues)
- **Private:** Email team members

---

## 📄 License

By contributing, you agree your contributions will be licensed under the same license as the project (Academic Use License).

---

**Thank you for contributing! 🎉**