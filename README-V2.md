# ResearchAssistantGPT

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-Academic-green.svg)]()

> AI-powered research assistant with RAG and multi-agent workflows for academic literature review

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Course Context](#-course-context)
- [Key Features](#-key-features)
- [Technical Stack](#%EF%B8%8F-technical-stack)
- [Architecture](#%EF%B8%8F-architecture)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Documentation](#-documentation)
- [Development](#%EF%B8%8F-development)
- [Team](#-team)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

ResearchAssistantGPT is a **RAG-based research assistant** that generates **cited summaries** from academic papers using multi-agent AI workflows. The system combines retrieval-augmented generation with fact-checking agents to ensure accuracy and proper citation.

---

## 🎓 Course Context

**Course**: BIS5151 – Generative Artificial Intelligence  
**Institution**: Hochschule Pforzheim  
**Program**: Master of Information Systems  
**Semester**: Winter 2025/26  
**Instructor**: Prof. Dr. Manuel Fritz, MBA

This project demonstrates practical application of:
- Retrieval-Augmented Generation (RAG)
- Multi-agent AI systems
- LLM orchestration and governance
- AI evaluation frameworks

---

## ✨ Key Features

### Core Capabilities
- 📚 **Automatic Literature Ingestion**
  - ArXiv paper fetching with metadata
  - Local file processing (PDF, TXT)
  - Deduplication and versioning
  
- 🔍 **Hybrid Search & Retrieval**
  - Vector similarity search (semantic)
  - BM25 keyword search (lexical)
  - Combined hybrid ranking
  
- 🤖 **Multi-Agent Workflow**
  - **Writer Agent**: Drafts summaries from context
  - **Reviewer Agent**: Improves clarity and structure
  - **FactChecker Agent**: Validates claims against sources
  
- ✅ **Quality Assurance**
  - Citation validation ([1], [2] format)
  - Fact-checking against retrieved documents
  - Guardrails for harmful content (experimental)
  
- 🌐 **Multilingual Support**
  - English, German, French, Spanish
  - Maintains citation format across languages
  
- 🔒 **Privacy-Preserving**
  - Runs entirely on local infrastructure
  - No external API calls (except ArXiv)
  - Full data control

### Advanced Features
- 🔄 **Workflow Automation** (n8n)
  - Scheduled ingestion
  - Batch processing
  - Email/webhook notifications
  
- 📊 **Monitoring** (Experimental)
  - TruLens integration (coming soon)
  - Query logging
  - Performance metrics

---

## 🛠️ Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.11 | Core application |
| **RAG Framework** | Haystack 2.x | Document processing & retrieval |
| **Vector DB** | Weaviate | Semantic search |
| **Embeddings** | sentence-transformers | Text vectorization |
| **LLM** | Ollama (qwen2.5:3b) | Local inference |
| **Agents** | CrewAI | Multi-agent orchestration |
| **API Framework** | FastAPI | REST API |
| **Orchestration** | n8n | Workflow automation |
| **Database** | PostgreSQL | n8n persistence |
| **Containerization** | Docker Compose | Service orchestration |
| **Testing** | pytest, pytest-cov | Quality assurance |
| **Code Quality** | ruff, black, mypy | Linting & formatting |

---

## 🏗️ Architecture

### High-Level Flow
```
User/n8n Workflow
        ↓
    API Gateway (FastAPI)
        ↓
    CrewAI Service
        ↓
    ┌───────────┴───────────┐
    ↓                       ↓
RAG Pipeline            Ollama LLM
    ↓
Weaviate (Vector DB)
```

### Request Flow
```
1. User → n8n: Trigger workflow with research topic
2. n8n → API: POST /rag/query {"query": "...", "language": "en"}
3. API → CrewAI: Proxy request to agent service
4. CrewAI → RAG: Retrieve top-k relevant chunks
5. CrewAI → Ollama: Run multi-agent workflow:
   ├─ Writer: Draft summary from context
   ├─ Reviewer: Improve clarity
   └─ FactChecker: Verify claims against sources
6. CrewAI → API: Return fact-checked summary
7. API → n8n: Return final result
8. n8n → User: Deliver summary (email, webhook, etc.)
```

**📖 See [Architecture Documentation](docs/architecture/README.md) for detailed design**

---

## 📁 Project Structure
```
BIS5151E_Research-Assistant/
├── .devcontainer/              # VS Code DevContainer configuration
│   ├── Dockerfile              # Multi-stage build (dev, api, crewai)
│   └── devcontainer.json       # Container settings
│
├── .github/                    # GitHub configuration
│   ├── workflows/              
│   │   ├── ci.yml              # CI/CD pipeline
│   │   ├── docker-build.yml    # Docker image builds
│   │   └── release.yml         # Release automation
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   └── pull_request_template.md
│
├── configs/                    # Application configuration
│   └── app.yaml                # Main config (LLM, RAG, Weaviate)
│
├── data/                       # Data storage (gitignored)
│   ├── raw/                    # User-uploaded documents
│   ├── arxiv/                  # ArXiv papers
│   └── external/               # External datasets
│
├── docker/                     # Docker configuration
│   ├── docker-compose.yml      # Service definitions
│   └── .env.example            # Environment template
│
├── docs/                       # Documentation
│   ├── setup/                  # Installation guides
│   ├── api/                    # API reference
│   ├── architecture/           # System design
│   ├── examples/               # Usage examples
│   └── troubleshooting/        # Common issues
│
├── outputs/                    # Generated summaries (gitignored)
│
├── scripts/                    # Utility scripts
│   ├── admin/                  # Admin tools (backup, health check)
│   ├── dev/                    # Development helpers
│   ├── setup/                  # Setup scripts
│   └── manual/                 # Manual operations
│
├── src/                        # Source code
│   ├── agents/                 # CrewAI agents
│   │   ├── crews/              # Crew definitions
│   │   ├── tasks/              # Task definitions
│   │   └── runner.py           # Agent orchestration
│   │
│   ├── api/                    # FastAPI application
│   │   ├── routers/            # API endpoints
│   │   └── main.py             # API entrypoint
│   │
│   ├── eval/                   # Evaluation & safety
│   │   ├── guardrails.py       # Content safety checks
│   │   └── trulens.py          # Monitoring (experimental)
│   │
│   ├── rag/                    # RAG pipeline
│   │   ├── core/               # Pipeline & schema
│   │   ├── ingestion/          # Document processing
│   │   └── sources/            # Data sources (ArXiv, local)
│   │
│   └── utils/                  # Shared utilities
│
├── tests/                      # Test suite
│   ├── unit/                   # Fast, isolated tests
│   ├── integration/            # E2E tests (requires Docker)
│   ├── fixtures/               # Test data
│   └── conftest.py             # Pytest configuration
│
├── .env.example                # Application environment template
├── .gitignore                  # Git ignore rules
├── .ruff.toml                  # Ruff configuration
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # Academic license
├── QUICKSTART.md               # Quick installation guide
├── README.md                   # This file
├── ROADMAP.md                  # Future plans
└── requirements.txt            # Python dependencies
```

---

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** (with 16GB+ RAM allocated)
- **Git**
- **20GB free disk space**

### Installation (4 steps)

**Step 1: Clone and configure**
```bash
git clone https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git
cd BIS5151E_Research-Assistant

cp .env.example .env
cp docker/.env.example docker/.env
# Edit docker/.env: Set POSTGRES_PASSWORD and N8N_ENCRYPTION_KEY
```

**Step 2: Start services**
```bash
docker compose -f docker/docker-compose.yml up -d
```

**Step 3: Verify installation**
```bash
python scripts/admin/health_check.py
```

**Step 4: First query**
```bash
# Ingest sample papers
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "max_results": 3}'

# Query the system
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "language": "en"}'
```

**🎉 Done!** See [QUICKSTART.md](QUICKSTART.md) for detailed guide.

---

## 📊 Usage Examples

### Python API

**Ingest documents:**
```python
from src.rag.ingestion import IngestionEngine
from src.rag.sources import LocalFileSource

engine = IngestionEngine()
source = LocalFileSource("data/raw")
result = engine.ingest_from_source(source)

print(f"Ingested {result.chunks_ingested} chunks from {result.documents_loaded} documents")
```

**Query RAG:**
```python
from src.rag.core import RAGPipeline

pipeline = RAGPipeline.from_existing()
docs = pipeline.run(query="What is AI?", top_k=5)

for doc in docs:
    print(f"Source: {doc.meta['source']}")
    print(f"Content: {doc.content[:200]}...")
```

**Run multi-agent workflow:**
```python
from src.agents.runner import CrewRunner

runner = CrewRunner()
result = runner.run(
    topic="Explain transformer architecture",
    language="en"
)

print(result.final_output)
```

### REST API

**Ingest from ArXiv:**
```bash
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{
    "query": "retrieval augmented generation",
    "max_results": 5
  }'
```

**Query with agents:**
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "language": "en"
  }'
```

**Get statistics:**
```bash
curl http://localhost:8000/rag/stats
```

### CLI Tools

**Ingest local files:**
```bash
docker compose exec api python -m src.rag.cli ingest-local --pattern "*.pdf"
```

**Query from command line:**
```bash
docker compose exec api python -m src.rag.cli query "What is digital transformation?"
```

**Reset index:**
```bash
docker compose exec api python -m src.rag.cli reset-index --yes
```

---

## 📚 Documentation

### Getting Started
- **[Quickstart Guide](QUICKSTART.md)** - Get running in 10 minutes
- **[Installation](docs/setup/README.md)** - Detailed setup instructions
- **[Docker Setup](docs/setup/DOCKER.md)** - Container configuration

### Development
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Development Setup](docs/setup/DEVELOPMENT.md)** - Dev environment
- **[Testing Guide](tests/TESTING.md)** - Running tests
- **[Code Examples](docs/examples/README.md)** - Usage examples

### System Documentation
- **[Architecture](docs/architecture/README.md)** - System design
- **[API Reference](docs/api/README.md)** - Complete endpoint docs
- **[RAG Pipeline](docs/architecture/RAG_PIPELINE.md)** - Retrieval details
- **[Agent System](docs/architecture/AGENTS.md)** - CrewAI workflows

### Operations
- **[Troubleshooting](docs/troubleshooting/README.md)** - Common issues
- **[n8n Workflows](docs/examples/workflow_examples.md)** - Automation examples
- **[Roadmap](ROADMAP.md)** - Future features

### Quick Links
- **API Docs (Swagger)**: http://localhost:8000/docs
- **n8n UI**: http://localhost:5678
- **Weaviate Console**: http://localhost:8080/v1/meta

---

## 🛠️ Development

### DevContainer Setup
```bash
# Open in VS Code
code .
# VS Code will prompt: "Reopen in Container"
```

### Run Tests
```bash
# All tests
pytest tests/ -v

# Unit only (fast)
pytest tests/unit/ -v

# Integration (requires Docker)
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality
```bash
# Format
black src tests

# Lint
ruff check src tests --fix

# Type check
mypy src
```

### Commit Standards
We use [Conventional Commits](https://www.conventionalcommits.org/):
```bash
git commit -m "feat: add German language support"
git commit -m "fix: resolve Weaviate timeout issue"
git commit -m "docs: update API examples"
```

**See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines**

---

## 👥 Team

| Name | Role | GitHub |
|------|------|--------|
| Jason Warzecha | Project Lead | [@Jasonwts-x](https://github.com/Jasonwts-x) |
| [Team Member 2] | RAG Engineer | [@username](https://github.com/username) |
| [Team Member 3] | Agent Developer | [@username](https://github.com/username) |
| [Team Member 4] | Integration Lead | [@username](https://github.com/username) |

---

## 🤝 Contributing

Contributions are welcome! Please see:
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [ROADMAP.md](ROADMAP.md) - Future plans
- [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues) - Report bugs or request features

---

## 📄 License

Academic use only. This project is part of the BIS5151 course at Hochschule Pforzheim.

See [LICENSE](LICENSE) for details.

---

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/discussions)

---

**Made with ❤️ for BIS5151 @ Hochschule Pforzheim**