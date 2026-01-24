# Development Setup Guide

Complete guide for setting up a development environment.

---

## Prerequisites

- Docker Desktop installed
- VS Code (recommended)
- Git
- Basic Python knowledge

---

## Development Environments

### Option 1: DevContainer (Recommended)

**Pros:**
- ✅ Consistent environment for all developers
- ✅ All dependencies pre-installed
- ✅ Integrated with Docker services
- ✅ No local Python setup needed

**Setup:**

1. **Install VS Code extensions:**
   - Dev Containers (ms-vscode-remote.remote-containers)

2. **Open project in VS Code:**
```bash
   code .
```

3. **Reopen in container:**
   - VS Code will prompt: "Reopen in Container"
   - Click it
   - Wait 2-3 minutes for container to build

4. **Verify setup:**
```bash
   # Inside container terminal
   python --version  # Should be 3.11
   which python      # Should be /usr/local/bin/python
   pip list          # Should show all dependencies
```

**Container features:**
- Python 3.11
- All project dependencies
- Ruff, Black, MyPy
- pytest
- Git
- Access to all Docker services

---

### Option 2: Local Python Environment

**For those who prefer local development.**

**Setup:**

1. **Install Python 3.11:**
```bash
   # macOS (Homebrew)
   brew install python@3.11
   
   # Windows (Chocolatey)
   choco install python --version=3.11
   
   # Linux (apt)
   sudo apt-get install python3.11 python3.11-venv
```

2. **Create virtual environment:**
```bash
   python3.11 -m venv .venv
   
   # Activate
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
```

3. **Install dependencies:**
```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
```

4. **Configure environment:**
```bash
   cp .env.example .env
   # Edit .env with your settings
```

5. **Set PYTHONPATH:**
```bash
   # macOS/Linux (add to ~/.bashrc or ~/.zshrc)
   export PYTHONPATH=/path/to/BIS5151E_Research-Assistant
   
   # Windows (PowerShell, add to $PROFILE)
   $env:PYTHONPATH = "C:\path\to\BIS5151E_Research-Assistant"
```

---

## Development Workflow

### 1. Start Services
```bash
# Start infrastructure
docker compose -f docker/docker-compose.yml up -d

# Or start specific services
docker compose up -d weaviate postgres ollama
```

### 2. Run Code Locally

**In DevContainer:**
```bash
# Already configured, just run:
python src/api/main.py

# Or
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**In local environment:**
```bash
# Make sure PYTHONPATH is set
export PYTHONPATH=$(pwd)

# Run API
python src/api/main.py
```

### 3. Make Changes
```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes
code src/agents/crews/research_crew.py

# Test changes
pytest tests/unit/test_agents/
```

### 4. Format & Lint
```bash
# Format code
black src tests

# Lint
ruff check src tests --fix

# Type check
mypy src
```

### 5. Run Tests
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/unit/test_rag/test_processor.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 6. Commit Changes
```bash
# Stage changes
git add src/agents/crews/research_crew.py
git add tests/unit/test_agents/test_research_crew.py

# Commit with conventional commit message
git commit -m "feat: add confidence scoring to agents"

# Push
git push origin feature/your-feature
```

### 7. Create Pull Request

1. Go to GitHub
2. Create Pull Request from your branch
3. Fill in PR template
4. Request review

---

## Development Tools

### Code Formatting

**Black** - Opinionated code formatter
```bash
# Format all code
black src tests

# Check without modifying
black --check src tests

# Format specific file
black src/agents/runner.py
```

**Configuration:** Uses defaults (line length: 88)

---

### Linting

**Ruff** - Fast Python linter
```bash
# Lint all code
ruff check src tests

# Auto-fix issues
ruff check src tests --fix

# Lint specific file
ruff check src/rag/core/pipeline.py
```

**Configuration:** `.ruff.toml`
```toml
[lint]
select = ["E", "F", "W", "I", "N"]
ignore = ["E501"]  # Line too long (handled by Black)

[format]
line-length = 88
```

---

### Type Checking

**MyPy** - Static type checker
```bash
# Type check all code
mypy src

# Strict mode
mypy src --strict

# Specific file
mypy src/rag/core/pipeline.py
```

**Configuration:** `pyproject.toml` (to be added)
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

---

### Testing

**pytest** - Testing framework
```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/unit/test_rag/test_processor.py::test_chunk_text -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term --cov-report=html

# Run only unit tests (fast)
pytest tests/unit/ -v

# Run only integration tests (slow)
pytest tests/integration/ -v

# Run with markers
pytest -m "not slow" tests/
```

**Useful flags:**
- `-v` - Verbose output
- `-s` - Show print statements
- `-x` - Stop on first failure
- `--pdb` - Drop into debugger on failure
- `--lf` - Run only last failed tests
- `--tb=short` - Shorter traceback format

---

## Debugging

### VS Code Debugger

**Configuration:** `.vscode/launch.json`
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.api.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "tests/",
        "-v"
      ],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

**Usage:**
1. Set breakpoints in code (click left of line number)
2. Press F5 or Run → Start Debugging
3. Select configuration (e.g., "Python: FastAPI")
4. Debugger will stop at breakpoints

---

### Print Debugging
```python
import logging

logger = logging.getLogger(__name__)

def process_document(doc):
    logger.info(f"Processing document: {doc.meta['source']}")
    logger.debug(f"Document content length: {len(doc.content)}")
    
    # Processing...
    
    logger.info(f"Generated {len(chunks)} chunks")
    return chunks
```

**Configure logging level:**
```bash
# In .env
LOG_LEVEL=DEBUG  # Show all logs
LOG_LEVEL=INFO   # Show info and above (default)
LOG_LEVEL=WARNING  # Show warnings and errors only
```

---

### Interactive Python Shell
```bash
# Start Python shell with project context
python

>>> from src.rag.core import RAGPipeline
>>> pipeline = RAGPipeline.from_existing()
>>> docs = pipeline.run("test query", top_k=3)
>>> print(docs[0].content)
```

**Or use IPython (better):**
```bash
pip install ipython
ipython

In [1]: from src.rag.core import RAGPipeline
In [2]: pipeline = RAGPipeline.from_existing()
In [3]: pipeline?  # Show docstring
```

---

## Testing Best Practices

### Test Structure
```python
# tests/unit/test_rag/test_processor.py
import pytest
from src.rag.ingestion.processor import DocumentProcessor

class TestDocumentProcessor:
    """Test suite for DocumentProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance for testing."""
        return DocumentProcessor()
    
    def test_chunk_text_basic(self, processor):
        """Test basic text chunking."""
        text = "This is a test. " * 100
        chunks = processor.chunk_text(text, chunk_size=200)
        
        assert len(chunks) > 0
        assert all(len(c) <= 200 for c in chunks)
    
    def test_chunk_id_deterministic(self, processor):
        """Test that chunk IDs are deterministic."""
        chunk = "Test content"
        id1 = processor.generate_chunk_id(chunk, "source.pdf", 0)
        id2 = processor.generate_chunk_id(chunk, "source.pdf", 0)
        
        assert id1 == id2
    
    def test_chunk_empty_text(self, processor):
        """Test handling of empty text."""
        chunks = processor.chunk_text("", chunk_size=200)
        assert len(chunks) == 0
```

### Fixtures
```python
# tests/conftest.py
import pytest
from src.rag.core import RAGPipeline

@pytest.fixture
def weaviate_client():
    """Create Weaviate client for testing."""
    import weaviate
    client = weaviate.Client("http://localhost:8080")
    yield client
    # Cleanup after test
    client.close()

@pytest.fixture
def sample_document():
    """Create sample document for testing."""
    from haystack.dataclasses import Document
    return Document(
        content="This is a test document.",
        meta={"source": "test.pdf"}
    )
```

### Markers
```python
# Mark slow tests
@pytest.mark.slow
def test_large_ingestion():
    ...

# Mark integration tests
@pytest.mark.integration
def test_full_pipeline():
    ...

# Run with: pytest -m "not slow" tests/
```

---

## Common Development Tasks

### Add New Endpoint

1. **Create router function:**
```python
   # src/api/routers/rag.py
   @router.post("/rag/new-endpoint")
   def new_endpoint(payload: NewRequest) -> NewResponse:
       """Documentation here."""
       # Implementation
       return NewResponse(...)
```

2. **Add request/response models:**
```python
   class NewRequest(BaseModel):
       field1: str
       field2: int
   
   class NewResponse(BaseModel):
       result: str
```

3. **Write tests:**
```python
   # tests/unit/test_api/test_rag.py
   def test_new_endpoint():
       response = client.post("/rag/new-endpoint", json={...})
       assert response.status_code == 200
```

4. **Update API docs:**
```markdown
   # docs/api/README.md
   ### POST /rag/new-endpoint
   ...
```

---

### Add New Agent

1. **Define agent:**
```python
   # src/agents/config/agents.yaml
   new_agent:
     role: "New Agent Role"
     goal: "Agent goal"
     backstory: "Agent backstory"
```

2. **Create task:**
```python
   # src/agents/config/tasks.yaml
   new_task:
     description: "Task description"
     expected_output: "Expected output format"
```

3. **Update crew:**
```python
   # src/agents/crews/research_crew.py
   new_agent = Agent(
       role=self.agents_config['new_agent']['role'],
       ...
   )
```

4. **Test:**
```python
   # tests/unit/test_agents/test_new_agent.py
   def test_new_agent():
       ...
```

---

### Update Dependencies
```bash
# Add new dependency
pip install new-package

# Update requirements.txt
pip freeze | grep new-package >> requirements.txt

# Or manually edit requirements.txt
echo "new-package==1.2.3" >> requirements.txt

# Rebuild DevContainer
# Cmd+Shift+P → "Dev Containers: Rebuild Container"
```

---

## Git Workflow

### Branch Naming
```
feature/add-caching-layer
fix/weaviate-connection-timeout
docs/update-api-examples
refactor/simplify-ingestion
test/add-integration-tests
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
feat: add confidence scoring to FactChecker agent
fix: resolve memory leak in embedding generation
docs: update API documentation with new endpoint
style: format code with black
refactor: simplify RAG pipeline initialization
test: add unit tests for document processor
chore: update dependencies
```

**Scope (optional):**
```
feat(agents): add translator agent
fix(rag): resolve Weaviate timeout
docs(api): add webhook examples
```

---

## Performance Profiling

### Memory Profiling
```python
from memory_profiler import profile

@profile
def my_function():
    # Your code here
    pass

# Run with: python -m memory_profiler script.py
```

### Time Profiling
```python
import cProfile
import pstats

cProfile.run('my_function()', 'profile.stats')
stats = pstats.Stats('profile.stats')
stats.sort_stats('cumulative')
stats.print_stats(10)
```

**Or use line_profiler:**
```bash
pip install line_profiler

# Add @profile decorator
@profile
def my_function():
    ...

# Run
kernprof -l -v script.py
```

---

## Continuous Integration

### Local CI Checks

Run the same checks that CI will run:
```bash
# Format check
black --check src tests

# Lint
ruff check src tests

# Type check
mypy src

# Unit tests
pytest tests/unit/ -v

# All together
make ci  # If Makefile exists
```

---

## Troubleshooting Development Issues

### Issue: Import Errors
```python
# ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Set PYTHONPATH
export PYTHONPATH=$(pwd)

# Or in VS Code, add to settings.json:
{
  "terminal.integrated.env.linux": {
    "PYTHONPATH": "${workspaceFolder}"
  }
}
```

---

### Issue: Tests Can't Connect to Services

**Solution:**
```bash
# Make sure services are running
docker compose ps

# Start services if needed
docker compose up -d weaviate postgres ollama
```

---

### Issue: Black and Ruff Conflict

**Solution:**
```bash
# Run in this order:
black src tests  # Format first
ruff check src tests --fix  # Then lint
```

---

## Resources

- **Python Style Guide:** [PEP 8](https://pep8.org/)
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **pytest Docs:** https://docs.pytest.org/
- **Haystack Docs:** https://docs.haystack.deepset.ai/
- **CrewAI Docs:** https://docs.crewai.com/

---

**[⬅ Back to Setup](README.md)** | **[⬆ Back to Main README](../../README.md)**