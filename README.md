# Research-Assistant-GPT

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-Academic-green.svg)](LICENSE)

> AI-powered research assistant with RAG and multi-agent workflows for academic literature review

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Course Context](#-course-context)
- [Project Objectives](#-project-objectives)
- [Key Features](#-key-features)
- [Technical Stack](#%EF%B8%8F-technical-stack)
- [System Architecture](#%EF%B8%8F-system-architecture)
- [Folder Structure](#-folder-structure)
- [Getting Started](#-getting-started)
- [Documentation](#-documentation)
- [Evaluation & Quality](#-evaluation--quality)
- [Team](#-team)
- [License](#-license)

---

## 🎯 Overview

ResearchAssistantGPT is a **RAG-based research assistant** that generates **cited summaries** from academic papers using multi-agent AI workflows. 
The system combines retrieval-augmented generation with fact-checking agents to ensure accuracy and proper citation.

Built as a course project for BIS5151 (Generative AI) at Hochschule Pforzheim, this system demonstrates practical application of modern AI techniques in an academic context.

---

## 🎓 Course Context

**Course**: BIS5151 – Generative Artificial Intelligence  
**Institution**: Hochschule Pforzheim  
**Program**: Master of Information Systems  
**Semester**: Winter 2025/26  
**Instructor**: Prof. Dr. Manuel Fritz, MBA

This project demonstrates practical application of:
- Retrieval-Augmented Generation (RAG)
- Multi-agent AI systems (CrewAI)
- LLM orchestration with n8n
- AI evaluation frameworks (TruLens, Guardrails)
- Docker microservices architecture

---

## 🎯 Project Objectives

### Core Objectives
1. **Literature Retrieval**: Fetch and index academic papers from ArXiv and local sources
2. **Context-Aware Summarization**: Generate 300-word summaries grounded in source documents
3. **Fact Verification**: Validate all claims against retrieved sources with FactChecker agent
4. **Citation Discipline**: Ensure proper citation with [1], [2], etc. markers
5. **Multilingual Support**: Summarize in English, German, French, and Spanish
6. **Quality Assurance**: Implement evaluation metrics and safety guardrails

### Technical Objectives
1. **Microservices Architecture**: Separate services for API, agents, RAG, and orchestration
2. **Hybrid Retrieval**: Combine BM25 lexical search with semantic vector search
3. **Agent Collaboration**: Multi-agent workflow (Writer → Reviewer → FactChecker)
4. **Scalability**: Docker-based deployment ready for production
5. **Privacy**: Run entirely on local infrastructure (no external API calls)

---

## ✨ Key Features

- 📚 **Automatic Ingestion** - Fetch papers from ArXiv or ingest local PDFs/TXT files
- 🔍 **Hybrid Search** - BM25 + vector similarity using Weaviate vector database
- 🤖 **Multi-Agent System** - Three specialized agents (Writer, Reviewer, FactChecker)
- ✅ **Fact Checking** - Validate claims against source documents
- 📝 **Citation Management** - Automatic citation insertion and validation
- 🌐 **Multilingual** - Summarize in EN, DE, FR, ES
- 🔒 **Privacy-First** - Runs entirely locally (no data leaves your machine)
- 🐳 **Docker-Native** - One-command deployment with Docker Compose
- 🔄 **n8n Orchestration** - Workflow automation for scheduled tasks
- 📊 **Quality Monitoring** - TruLens evaluation and Guardrails safety checks (experimental)

---

## 🛠️ Technical Stack

### Core Services (Docker Compose)

| Service | Technology | Purpose | Port |
|---------|-----------|---------|------|
| **API Gateway** | FastAPI + Uvicorn | Main REST API | 8000 |
| **CrewAI Service** | CrewAI 1.3.0 | Multi-agent workflow | 8100 |
| **Vector Database** | Weaviate 1.23.0 | Hybrid search (BM25 + vector) | 8080 |
| **LLM Runtime** | Ollama | Local LLM inference | 11434 |
| **Orchestrator** | n8n | Workflow automation | 5678 |
| **Database** | PostgreSQL 15 | n8n persistence | 5432 |
| **DevContainer** | Python 3.11 | Development environment | - |

### Python Libraries

**Core Framework**:
- **Haystack 2.x** - RAG pipeline framework
- **CrewAI 1.3.0** - Multi-agent collaboration
- **FastAPI** - Modern async API framework
- **Uvicorn** - ASGI server
- **Pydantic 2.x** - Data validation

**AI/ML**:
- **LangChain-Ollama** - LLM integration
- **sentence-transformers** - Text embeddings (`all-MiniLM-L6-v2`)
- **weaviate-client** - Vector database client
- **haystack-weaviate** - Weaviate document store

**Data Processing**:
- **PyPDF** - PDF parsing
- **arxiv** - ArXiv API client
- **requests** - HTTP client
- **python-dotenv** - Environment management

**Evaluation** (Experimental):
- **trulens-eval 0.19.0** - RAG quality metrics
- **guardrails-ai** - Input/output validation
- **rouge-score** - Summarization metrics
- **sacrebleu** - Translation quality (BLEU)

**Development**:
- **pytest** - Testing framework
- **ruff** - Fast Python linter
- **black** - Code formatter
- **mypy** - Type checking

### LLM Configuration

**Default Model**: `qwen3:1.7b` (Qwen 2.5 - 1.7B parameters)  
**Alternatives**: `qwen3:4b`, `qwen2.5:3b`, `llama3.2:3b`  
**Why Qwen?**: Balanced speed/quality for local inference, strong multilingual support

**Note**: The model can be changed in `docker/.env` by setting `OLLAMA_MODEL`.

---

## 🏛️ System Architecture

### High-Level Architecture
```
┌────────────────────────────────────────────────────────────────┐
│                         External Layer                         │
│  ┌────────────┐                              ┌──────────────┐  │
│  │    User    │                              │   n8n UI     │  │
│  │  (Browser) │                              │  (Workflow)  │  │
│  └─────┬──────┘                              └──────┬───────┘  │
└────────┼────────────────────────────────────────────┼──────────┘
         │                                            │
         └────────────────────┬───────────────────────┘
                              │
┌─────────────────────────────┼──────────────────────────────────┐
│                    Application Layer                           │
│                              │                                 │
│                    ┌─────────▼──────────┐                      │
│                    │   API Gateway      │                      │
│                    │   (FastAPI:8000)   │                      │
│                    └─────────┬──────────┘                      │
│                              │                                 │
│          ┌───────────────────┼──────────────────┐              │
│          │                   │                  │              │
│    ┌─────▼──────┐   ┌───────▼────────┐  ┌─────▼────────┐       │
│    │    RAG     │   │  CrewAI Service│  │    Ollama    │       │
│    │  Pipeline  │   │    (:8100)     │  │   (:11434)   │       │
│    └─────┬──────┘   └───────┬────────┘  └──────────────┘       │
└──────────┼──────────────────┼──────────────────────────────────┘
           │                  │
┌──────────┼──────────────────┼──────────────────────────────────┐
│                         Data Layer                             │
│    ┌─────▼──────────────┐   │                                  │
│    │     Weaviate       │   │                                  │
│    │  Vector Database   │   │                                  │
│    │     (:8080)        │   │                                  │
│    └────────────────────┘   │                                  │
│                             │                                  │
│    ┌────────────────────────▼───┐                              │
│    │      PostgreSQL            │                              │
│    │  (n8n + TruLens DB)        │                              │
│    │        (:5432)             │                              │
│    └────────────────────────────┘                              │
└────────────────────────────────────────────────────────────────┘┌────────────────────────────────────────────────────────────────┐
│                         External Layer                         │
│  ┌────────────┐                              ┌──────────────┐  │
│  │    User    │                              │   n8n UI     │  │
│  │  (Browser) │                              │  (Workflow)  │  │
│  └─────┬──────┘                              └──────┬───────┘  │
└────────┼────────────────────────────────────────────┼──────────┘
         │                                            │
         └────────────────────┬───────────────────────┘
                              │
┌─────────────────────────────┼──────────────────────────────────┐
│                    Application Layer                           │
│                              │                                 │
│                    ┌─────────▼──────────┐                      │
│                    │   API Gateway      │                      │
│                    │   (FastAPI:8000)   │                      │
│                    └─────────┬──────────┘                      │
│                              │                                 │
│          ┌───────────────────┼──────────────────┐              │
│          │                   │                  │              │
│    ┌─────▼──────┐   ┌───────▼────────┐  ┌─────▼────────┐       │
│    │    RAG     │   │  CrewAI Service│  │    Ollama    │       │
│    │  Pipeline  │   │    (:8100)     │  │   (:11434)   │       │
│    └─────┬──────┘   └───────┬────────┘  └──────────────┘       │
└──────────┼──────────────────┼──────────────────────────────────┘
           │                  │
┌──────────┼──────────────────┼──────────────────────────────────┐
│                         Data Layer                             │
│    ┌─────▼──────────────┐   │                                  │
│    │     Weaviate       │   │                                  │
│    │  Vector Database   │   │                                  │
│    │     (:8080)        │   │                                  │
│    └────────────────────┘   │                                  │
│                             │                                  │
│    ┌────────────────────────▼───┐                              │
│    │      PostgreSQL            │                              │
│    │  (n8n + TruLens DB)        │                              │
│    │        (:5432)             │                              │
│    └────────────────────────────┘                              │
└────────────────────────────────────────────────────────────────┘
```

### Request Flow

**Complete Research Query Workflow**:
```
1. User → n8n: Trigger workflow with research topic

2. n8n → API: POST /rag/ingest/arxiv 
   └─> Fetch papers from ArXiv matching query
   └─> Extract text, chunk, embed, store in Weaviate

3. n8n → API: POST /research/query {"query": "...", "language": "en"}
   └─> API validates input with Guardrails

4. API → CrewAI: POST /crewai/run (proxy request)
   
5. CrewAI → Weaviate: Retrieve top-k relevant chunks
   └─> Hybrid search (BM25 + vector similarity)
   └─> Returns: 5-10 most relevant document chunks

6. CrewAI → Ollama: Run multi-agent workflow:
   ├─ Writer Agent: Draft 300-word summary from context
   ├─ Reviewer Agent: Improve clarity, fix grammar
   └─ FactChecker Agent: Verify claims against sources, validate citations

7. CrewAI → API: Return fact-checked summary with citations

8. API: Validate output with Guardrails
   └─> Check citation format, length, harmful content

9. API → n8n: Return final result

10. n8n → User: Deliver summary (email, webhook, notification, etc.)
```

**Data Flow Details**:
- **Ingestion**: ArXiv/Local → PDF Parse → Chunking (350 chars) → Embedding → Weaviate
- **Retrieval**: Query → Embed → Hybrid Search (α=0.5) → Top-5 chunks → Context
- **Generation**: Context → Writer → Reviewer → FactChecker → Final Summary

---

## 📁 Folder Structure
```
BIS5151E_Research-Assistant/
├── .devcontainer/              # VS Code DevContainer
│   ├── Dockerfile              # Multi-stage: dev, api, crewai
│   └── devcontainer.json       # Container settings
│
├── .github/                    # GitHub configuration
│   ├── workflows/              
│   │   └── ci.yml              # CI/CD pipeline
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   └── pull_request_template.md
│
├── configs/                    # Application configuration
│   └── app.yaml                # Main config (LLM, RAG, Weaviate, Guardrails)
│
├── data/                       # Data storage (gitignored except .gitkeep)
│   ├── raw/                    # Local PDFs/TXT files
│   ├── arxiv/                  # Downloaded ArXiv papers
│   ├── processed/              # Processed chunks (legacy)
│   └── external/               # External datasets
│
├── database/                   # Database scripts
│   ├── init/                   # PostgreSQL init scripts
│   └── scripts/                # Backup/restore scripts
│
├── docker/                     # Docker configuration
│   ├── docker-compose.yml      # Main services (CPU mode)
│   ├── docker-compose.nvidia.yml # GPU support (NVIDIA)
│   ├── docker-compose.amd.yml  # GPU support (AMD)
│   ├── .env.example            # Docker environment template
│   └── workflows/              # n8n workflow files
│       └── research_assistant.json
│
├── docs/                       # Documentation
│   ├── setup/                  # Installation & setup guides
│   │   ├── README.md           # Setup hub
│   │   ├── INSTALLATION.md     # Detailed installation
│   │   ├── GPU.md              # GPU setup
│   │   ├── N8N.md              # n8n workflow setup
│   │   └── TROUBLESHOOTING.md  # Common issues
│   ├── api/                    # API documentation
│   │   └── README.md           # Endpoint reference
│   ├── architecture/           # System design
│   │   ├── README.md           # Architecture overview
│   │   ├── DATA_FLOW.md        # Data flow diagrams
│   │   └── research-assistant_*.txt # Project docs
│   ├── examples/               # Usage examples
│   │   └── workflow_examples.md
│   ├── evaluation/             # Evaluation documentation
│   │   ├── README.md           # Evaluation overview
│   │   ├── TRULENS.md          # TruLens setup
│   │   └── METRICS.md          # Metrics explanation
│   └── templates/              # Chat templates for development
│
├── outputs/                    # Generated summaries (gitignored)
│
├── scripts/                    # Utility scripts
│   ├── admin/                  # Administration
│   │   └── health_check.py     # Service health checks
│   ├── eval/                   # Evaluation scripts
│   └── setup/                  # Setup helpers
│
├── src/                        # Source code
│   ├── agents/                 # CrewAI multi-agent system
│   │   ├── api/                # CrewAI service API (port 8100)
│   │   ├── roles/              # Agent definitions
│   │   ├── tasks/              # Task definitions
│   │   ├── crews/              # Crew compositions
│   │   └── runner.py           # Execution logic
│   ├── api/                    # Main API gateway (port 8000)
│   │   ├── routers/            # Endpoint groups
│   │   │   ├── crewai.py       # CrewAI proxy
│   │   │   ├── ollama.py       # Ollama proxy
│   │   │   ├── rag.py          # RAG operations
│   │   │   ├── research.py     # Research workflow
│   │   │   └── system.py       # Health/version
│   │   ├── schemas/            # Pydantic models
│   │   └── server.py           # FastAPI app
│   ├── eval/                   # Evaluation & monitoring
│   │   ├── guardrails/         # Safety validation
│   │   ├── trulens/            # Quality metrics
│   │   ├── performance/        # Performance tracking
│   │   └── quality/            # Quality metrics
│   ├── rag/                    # RAG pipeline (Haystack + Weaviate)
│   │   ├── core/               # Pipeline components
│   │   │   ├── docstore.py     # Weaviate document store
│   │   │   ├── embedder.py     # Sentence transformers
│   │   │   ├── pipeline.py     # RAG pipeline (singleton)
│   │   │   ├── processor.py    # Document processing
│   │   │   └── schema.py       # Weaviate schema (explicit)
│   │   ├── sources/            # Data sources
│   │   │   ├── arxiv.py        # ArXiv API client
│   │   │   └── local.py        # Local file loader
│   │   └── cli.py              # CLI entrypoint
│   └── utils/                  # Utilities
│       ├── config.py           # Configuration loader
│       └── logging_config.py   # Logging setup
│
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   │   ├── test_agents/        # Agent tests
│   │   ├── test_api/           # API tests
│   │   ├── test_eval/          # Evaluation tests
│   │   └── test_rag/           # RAG tests
│   ├── integration/            # Integration tests
│   ├── fixtures/               # Test data
│   ├── conftest.py             # Pytest configuration
│   └── TESTING.md              # Testing guide
│
├── .env.example                # Application environment template
├── .gitignore                  # Git ignore rules
├── .gitattributes              # Git attributes
├── .ruff.toml                  # Ruff linter config
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guide
├── LICENSE                     # Academic license
├── QUICKSTART.md               # 5-minute quickstart
├── README.md                   # This file
├── ROADMAP.md                  # Future plans
├── requirements.txt            # Python dependencies
└── requirements-dev.txt        # Development dependencies
```

---

## 🚀 Getting Started

### Quick Start (5 Minutes)

See **[QUICKSTART.md](QUICKSTART.md)** for the fastest path to running the system.

### Detailed Installation

See **[docs/setup/INSTALLATION.md](docs/setup/INSTALLATION.md)** for complete installation instructions.

**Prerequisites**:
- Docker Desktop
- 16GB RAM (32GB recommended)
- 20GB free disk space
- Windows 10/11, macOS, or Linux

**Quick Commands**:
```bash
# 1. Clone repository
git clone https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git
cd BIS5151E_Research-Assistant

# 2. Configure environment
cp .env.example .env
cp docker/.env.example docker/.env
# Edit docker/.env: Set POSTGRES_PASSWORD and N8N_ENCRYPTION_KEY

# 3. Start services
docker compose -f docker/docker-compose.yml up -d

# 4. Wait for services (2-3 minutes)
docker compose logs -f

# 5. Verify health
curl http://localhost:8000/health

# 6. First query
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "max_results": 3}'

curl -X POST http://localhost:8000/research/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "language": "en"}'
```

**Access Points**:
- **API Docs**: http://localhost:8000/docs
- **n8n UI**: http://localhost:5678
- **Weaviate**: http://localhost:8080/v1/meta

---

## 📚 Documentation

### **Main Documentation**

| Category | Document | Description |
|----------|----------|-------------|
| **Setup & Installation** | [QUICKSTART.md](QUICKSTART.md) | Get running in 5 minutes |
| | [docs/setup/](docs/setup/) | Complete installation guides |
| | [docs/setup/INSTALLATION.md](docs/setup/INSTALLATION.md) | Detailed step-by-step setup |
| | [docs/setup/GPU.md](docs/setup/GPU.md) | NVIDIA/AMD GPU acceleration |
| | [docs/setup/N8N.md](docs/setup/N8N.md) | n8n workflow automation setup |
| | [docs/setup/TROUBLESHOOTING.md](docs/setup/TROUBLESHOOTING.md) | Common issues & solutions |
| **API Reference** | [docs/api/](docs/api/) | Complete API documentation |
| | [Swagger UI](http://localhost:8000/docs) | Interactive API docs (when running) |
| **Architecture** | [docs/architecture/](docs/architecture/) | System design documents |
| | [docs/architecture/README.md](docs/architecture/README.md) | Architecture overview |
| | [docs/architecture/DATA_FLOW.md](docs/architecture/DATA_FLOW.md) | Request flow diagrams |
| **Usage Examples** | [docs/examples/](docs/examples/) | Code examples & workflows |
| | [docs/examples/workflow_examples.md](docs/examples/workflow_examples.md) | n8n workflow examples |
| **Evaluation** | [docs/evaluation/](docs/evaluation/) | Quality & monitoring |
| | [docs/evaluation/README.md](docs/evaluation/README.md) | Evaluation overview |
| | [docs/evaluation/METRICS.md](docs/evaluation/METRICS.md) | Metrics explanation |
| | [docs/evaluation/TRULENS.md](docs/evaluation/TRULENS.md) | TruLens setup guide |
| **Development** | [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| | [tests/TESTING.md](tests/TESTING.md) | Testing guide |
| **Project Info** | [CHANGELOG.md](CHANGELOG.md) | Version history |
| | [ROADMAP.md](ROADMAP.md) | Future plans |
| | [LICENSE](LICENSE) | License information |

---

## 📊 Evaluation & Quality

### Quality Metrics

The system implements comprehensive evaluation to ensure high-quality outputs:

| Metric | Purpose | Target | Status |
|--------|---------|--------|--------|
| **Answer Relevance** | Does the answer address the query? | > 0.8 | ✅ Implemented (TruLens) |
| **Context Relevance** | Is retrieved context useful? | > 0.7 | ✅ Implemented (TruLens) |
| **Groundedness** | Are claims supported by context? | > 0.85 | ✅ Implemented (TruLens) |
| **Citation Coverage** | % of claims with citations | > 90% | ✅ Implemented (Guardrails) |
| **ROUGE-L** | Summarization quality | > 0.5 | ✅ Implemented |
| **Response Time** | Query latency | < 30s | ✅ Measured |

### Guardrails (Safety Checks)

**Input Validation**:
- ✅ Query length limits (< 10,000 chars)
- ✅ Jailbreak attempt detection
- ✅ PII detection (basic)
- ✅ Off-topic query detection

**Output Validation**:
- ✅ Citation format checking
- ✅ Hallucination marker detection ("I think", "I believe", etc.)
- ✅ Length validation
- ✅ Harmful content filtering

### Evaluation Dashboard

**TruLens Dashboard** (Experimental):
- Real-time quality metrics
- Query-level analysis
- Performance trends
- Feedback collection

See [docs/evaluation/](docs/evaluation/) for setup instructions.

---

## 👥 Team

**Team Members**:
- Jason Waschtschenko - [@Jasonwts-x](https://github.com/Jasonwts-x)
- Karim Epple - [@karim1501](https://github.com/karim1501)

- Dilsat Bekil
- Rigon Rexha
- Eren Kaya

**Course**: BIS5151 – Generative Artificial Intelligence  
**Institution**: Hochschule Pforzheim  
**Semester**: Winter 2025/26

---

## 📄 License

This project is licensed under the **Academic Use License** for educational purposes at Hochschule Pforzheim.

**Key Terms**:
- ✅ Free to use for academic/educational purposes
- ✅ Modifications allowed (must be documented)
- ❌ Commercial use prohibited without permission
- ⚠️ Must provide attribution in academic work

See [LICENSE](LICENSE) for full terms.

For commercial licensing inquiries, contact: waschtsc@hs-pforzheim.de

---

## 🙏 Acknowledgments

**Technologies**:
- [Haystack](https://haystack.deepset.ai/) - RAG framework
- [CrewAI](https://www.crewai.com/) - Multi-agent orchestration
- [Weaviate](https://weaviate.io/) - Vector database
- [Ollama](https://ollama.com/) - Local LLM runtime
- [n8n](https://n8n.io/) - Workflow automation
- [FastAPI](https://fastapi.tiangolo.com/) - API framework

**Course Instructor**:
- Prof. Dr. Manuel Fritz, MBA - For guidance and support

---

**[⬆ Back to Top](#researchassistantgpt)**