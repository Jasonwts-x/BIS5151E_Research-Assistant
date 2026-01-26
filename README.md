# ResearchAssistantGPT

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-Academic-green.svg)]()

> AI-powered research assistant with RAG and multi-agent workflows for academic literature review

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Course Context](#-course-context)
- [Project Objectives](#-project-objectives)
- [Technical Stack](#%EF%B8%8F-technical-stack)
- [Architecture](#%EF%B8%8F-architecture)
- [Folder Structure](#-folder-structure)
- [Quick Start](#-quick-start)
- [Documentation](#-documentation)
- [Development](#%EF%B8%8F-development)
- [Usage Examples](#-usage-examples)
- [Team](#-team)
- [License](#-license)

---

## 🎯 Overview

ResearchAssistantGPT is a **RAG-based research assistant** that generates **cited summaries** from academic papers using multi-agent AI workflows. The system combines retrieval-augmented generation with fact-checking agents to ensure accuracy and proper citation.

**Key Features**:
- 📚 **Automatic literature ingestion** from ArXiv and local files
- 🔍 **Hybrid retrieval** using Weaviate vector database
- 🤖 **Multi-agent workflow** (Writer → Reviewer → FactChecker)
- ✅ **Citation validation** and fact-checking
- 🌐 **Multilingual support** (English, German, French, Spanish)
- 🔒 **Privacy-preserving** (runs entirely on local infrastructure)

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

## 🎯 Project Objectives

### Core Objectives
1. **Literature Retrieval**: Fetch and index academic papers from ArXiv and local sources
2. **Context-Aware Summarization**: Generate 300-word summaries grounded in source documents
3. **Fact Verification**: Validate all claims against retrieved sources
4. **Citation Discipline**: Ensure proper attribution with [1], [2], etc. markers
5. **Quality Assurance**: Implement evaluation frameworks (TruLens, Guardrails AI)

### Learning Goals
- Hands-on experience with modern RAG architectures
- Understanding of agent-based AI systems (CrewAI)
- Practical knowledge of LLM evaluation and governance
- Workflow orchestration with n8n

---

## 🛠️ Technical Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.11 | Core development |
| **API Framework** | FastAPI + Uvicorn | REST API gateway |
| **RAG Framework** | Haystack 2.x | Document processing & retrieval |
| **Vector Database** | Weaviate | Hybrid search (lexical + semantic) |
| **LLM Runtime** | Ollama (qwen2.5:3b) | Local inference |
| **Agent Framework** | CrewAI 1.3.0 | Multi-agent orchestration |
| **Workflow Engine** | n8n | End-to-end automation |
| **Database** | PostgreSQL 15 | n8n workflow storage |
| **Embeddings** | Sentence-Transformers | Document vectorization |
| **Evaluation** | TruLens + Guardrails AI | Quality assurance |
| **Containerization** | Docker + Docker Compose | Service orchestration |

### Python Libraries
```python
crewai==1.3.0                # Multi-agent framework
haystack-ai==2.18.1          # RAG pipeline
weaviate-haystack==6.3.0     # Weaviate integration
langchain-ollama==1.0.1      # LLM integration
fastapi                      # Web framework
httpx                        # Async HTTP client
arxiv==2.1.0                # ArXiv paper fetching
```

---

## 🏗️ Architecture

### System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        n8n Orchestrator                     │
│                 Workflow Automation (Port 5678)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼──────────┐              ┌──────────▼─────────┐
│   API Gateway    │              │                    │
│   (FastAPI)      │◄─────────────┤   CrewAI Service   │
│   Port 8000      │  Proxy       │   Port 8100        │
└───────┬──────────┘              └──────────┬─────────┘
        │                                    │
    ┌───▼────────┐                      ┌───▼────────┐
    │            │                      │            │
    │  RAG       │                      │  Multi-    │
    │  Pipeline  │                      │  Agent     │
    │            │                      │  Workflow  │
    └───┬────────┘                      └───┬────────┘
        │                                   │
┌───────▼───────────────────────────────────▼──────────┐
│                                                      │
│  ┌─────────────┐        ┌──────────────┐            │
│  │  Weaviate   │        │   Ollama     │            │
│  │  Port 8080  │        │  Port 11434  │            │
│  │             │        │              │            │
│  │ • Hybrid    │        │ • LLM        │            │
│  │   Search    │        │   Inference  │            │
│  │ • Vector DB │        │ • qwen2.5:3b │            │
│  └─────────────┘        └──────────────┘            │
│                                                       │
│  ┌─────────────┐                                    │
│  │ PostgreSQL  │                                    │
│  │  Port 5432  │                                    │
│  │             │                                    │
│  │ • n8n DB    │                                    │
│  └─────────────┘                                    │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### Request Flow
```
1. User → n8n: Trigger workflow with research topic
2. n8n → API: POST /rag/query {"query": "...", "language": "en"}
3. API → CrewAI: POST /crew/run (proxy request)
4. CrewAI → Weaviate: Retrieve top-k relevant chunks
5. CrewAI → Ollama: Run multi-agent workflow:
   ├─ Writer: Draft summary from context
   ├─ Reviewer: Improve clarity
   └─ FactChecker: Verify claims against sources
6. CrewAI → API: Return fact-checked summary
7. API → n8n: Return final result
8. n8n → User: Deliver summary (email, webhook, etc.)
```

---

## 📁 Folder Structure
```
BIS5151E_Research-Assistant/
├── .devcontainer/              # VS Code DevContainer configuration
│   ├── Dockerfile              # Multi-stage build (dev, api, crewai)
│   └── devcontainer.json       # Container settings
│
├── .github/                    # GitHub configuration
│   ├── workflows/              
│   │   └── ci.yml              # CI/CD pipeline (pytest, ruff, black)
│   └── CODEOWNERS              # Code ownership
│
├── configs/                    # Application configuration
│   └── app.yaml                # Main config (LLM, RAG, Weaviate settings)
│
├── data/                       # Data storage (gitignored except .gitkeep)
│   ├── raw/                    # Source documents (PDFs, TXT)
│   ├── processed/              # Processed chunks
│   └── external/               # External datasets
│
├── docker/                     # Docker configuration
│   ├── docker-compose.yml      # Main service definitions
│   ├── docker-compose.nvidia.yml # GPU support (NVIDIA)
│   ├── docker-compose.amd.yml  # GPU support (AMD)
│   ├── .env.example            # Docker secrets template
│   └── workflows/              # n8n workflow files
│
├── docs/                       # Documentation
│   ├── setup/                  # Installation guides
│   ├── api/                    # API documentation
│   ├── architecture/           # Design documents
│   ├── examples/               # Usage examples
│   └── troubleshooting/        # Common issues
│
├── outputs/                    # Generated summaries (gitignored)
│
├── scripts/                    # Utility scripts
│   ├── admin/                  # Administrative tasks
│   │   ├── health_check.py     # Service health verification
│   │   ├── backup_data.sh      # Backup persistent data
│   │   └── cleanup_volumes.sh  # Docker cleanup
│   ├── dev/                    # Development helpers
│   │   ├── start_services.sh   # Start all services
│   │   ├── stop_services.sh    # Stop all services
│   │   └── restart_service.sh  # Restart specific service
│   ├── manual/                 # Manual testing scripts
│   └── setup/                  # Installation helpers
│       ├── verify_gpu.sh       # GPU detection
│       └── install_gpu_support_linux.sh
│
├── src/                        # Source code
│   ├── agents/                 # CrewAI multi-agent system
│   │   ├── api/                # CrewAI service (port 8100)
│   │   ├── config/             # Agent/task YAML configs
│   │   ├── crews/              # Crew compositions
│   │   ├── roles/              # Agent definitions
│   │   ├── tasks/              # Task definitions
│   │   ├── tools/              # Custom tools
│   │   └── runner.py           # Main execution logic
│   │
│   ├── api/                    # Main API gateway (port 8000)
│   │   ├── routers/            # Endpoint implementations
│   │   ├── schemas/            # Pydantic models
│   │   ├── dependencies.py     # Dependency injection
│   │   ├── errors.py           # Error handling
│   │   ├── openapi.py          # API documentation config
│   │   └── server.py           # FastAPI app
│   │
│   ├── eval/                   # Evaluation & quality assurance
│   │   ├── guardrails.py       # Safety checks
│   │   └── trulens.py          # Monitoring
│   │
│   ├── rag/                    # RAG pipeline
│   │   ├── core/               # Core infrastructure
│   │   │   ├── pipeline.py     # Main RAG pipeline
│   │   │   ├── schema.py       # Weaviate schema management
│   │   │   └── service.py      # RAG service layer
│   │   ├── ingestion/          # Document processing
│   │   │   ├── engine.py       # Ingestion orchestration
│   │   │   └── processor.py    # Chunking & ID generation
│   │   └── sources/            # Data sources
│   │       ├── base.py         # Abstract source
│   │       ├── local.py        # Local file source
│   │       └── arxiv.py        # ArXiv source
│   │
│   └── utils/                  # Shared utilities
│       └── config.py           # Configuration management
│
├── tests/                      # Test suite
│   ├── conftest.py             # Shared fixtures
│   ├── unit/                   # Unit tests
│   │   ├── test_rag/
│   │   ├── test_agents/
│   │   └── test_api/
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test data
│
├── .env.example                # Application environment template
├── .gitignore                  # Git ignore rules
├── .ruff.toml                  # Ruff linter config
├── CONTRIBUTING.md             # Contribution guidelines
├── README.md                   # This file
└── requirements.txt            # Python dependencies
```

---

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** (with 16GB+ RAM allocated)
- **Git**
- **20GB free disk space**

### Installation (5 steps)
```bash
# 1. Clone repository
git clone https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git
cd BIS5151E_Research-Assistant

# 2. Configure environment
cp .env.example .env
cp docker/.env.example docker/.env
# Edit docker/.env: Set POSTGRES_PASSWORD and N8N_ENCRYPTION_KEY

# 3. Start services (CPU mode)
docker compose -f docker/docker-compose.yml up -d

# 4. Verify installation
python scripts/admin/health_check.py

# 5. Ingest sample data
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "max_results": 3}'
```

### First Query
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "language": "en"
  }'
```

**See full installation guide**: [docs/setup/INSTALLATION.md](docs/setup/INSTALLATION.md)

---

## 📚 Documentation

- **[Installation Guide](docs/setup/INSTALLATION.md)** - Step-by-step setup
- **[API Documentation](docs/api/README.md)** - Endpoint reference
- **[Architecture](docs/architecture/README.md)** - System design
- **[Troubleshooting](docs/troubleshooting/README.md)** - Common issues
- **[Examples](docs/examples/README.md)** - Usage examples

**Quick Links**:
- API Docs (Swagger): http://localhost:8000/docs
- n8n UI: http://localhost:5678
- Weaviate Console: http://localhost:8080/v1/meta

---

## 🛠️ Development

### Open in DevContainer
```bash
# VS Code will detect .devcontainer/devcontainer.json
# Click "Reopen in Container"
```

### Run Tests
```bash
# All tests
pytest tests/ -v

# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests (requires services)
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality
```bash
# Format code
black src tests

# Lint
ruff check src tests --fix

# Type check
mypy src
```

### Commit Standards

We use **conventional commits**:
```
<feature>(<category>): <description>

Features: chore, docs, feat, fix, refactor, style, test
Categories: agents, api, docker, docs, rag, refactor, tests
Example: feat(agents): add translator agent for multilingual support
```

---

## 📊 Usage Examples

### API
```bash
# Ingest ArXiv papers
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "retrieval augmented generation", "max_results": 5}'

# Query with multi-agent processing
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "language": "en"
  }'

# Get index statistics
curl http://localhost:8000/rag/stats
```

### CLI
```bash
# Ingest local files
python -m src.rag.cli ingest-local --pattern "*.pdf"

# Fetch from ArXiv
python -m src.rag.cli ingest-arxiv "neural networks" --max-results 10

# Test retrieval
python -m src.rag.cli query "What is deep learning?" --top-k 5

# Reset index
python -m src.rag.cli reset-index --yes
```

---

## 📊 Evaluation & Monitoring

ResearchAssistantGPT includes comprehensive evaluation and monitoring:

### Evaluation Dashboard

Access the interactive dashboard at **http://localhost:8501** to view:
- TruLens quality metrics (groundedness, relevance)
- Guardrails validation results
- Performance timing breakdown
- ROUGE/BLEU quality scores

### Evaluation API

Query evaluation metrics programmatically:
```bash
# Get evaluation leaderboard
curl http://localhost:8502/metrics/leaderboard

# Get specific evaluation record
curl http://localhost:8502/metrics/record/{record_id}
```

### Evaluation in Query Responses

All query responses automatically include evaluation metrics:
```json
{
  "topic": "What is RAG?",
  "answer": "Retrieval-Augmented Generation...",
  "evaluation": {
    "trulens": {
      "groundedness": 0.85,
      "answer_relevance": 0.78,
      "context_relevance": 0.82
    },
    "guardrails": {
      "input_passed": true,
      "output_passed": true
    },
    "performance": {
      "total_time": 45.2,
      "rag_retrieval": 2.1,
      "crew_execution": 42.5
    }
  }
}
```

See [Evaluation Documentation](docs/evaluation/README.md) for details.

---

## 👥 Team

**Project Group**: ResearchAssistantGPT

- **Jason Waschtschenko** (GitHub: [@Jasonwts-x](https://github.com/Jasonwts-x))
- **Karim Epple**
- **Dilsat Bekil**
- **Rigon Rexha**
- **Eren Kaya**

---

## 📝 License

This project is for **educational use** within the Master of Information Systems program at Hochschule Pforzheim.

All AI models and datasets used comply with open-source or institutional usage rights.

---

## 🙏 Acknowledgments

- **Prof. Dr. Manuel Fritz, MBA** - Course instructor
- **Anthropic** - Claude AI assistance in development
- **Hochschule Pforzheim** - Academic support

---

**[⬆ Back to top](#researchassistantgpt)**

---