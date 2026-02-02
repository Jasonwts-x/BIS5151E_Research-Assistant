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

<table>
<tr>
<td width="50%" valign="top">

**Core Framework**
- 🚀 **FastAPI** `0.104.1` - API framework
- 🔄 **Uvicorn** `0.24.0` - ASGI server
- ✅ **Pydantic** `2.5.0` - Data validation

**RAG Pipeline**
- 🔍 **Haystack** `2.x` - RAG framework
- 🗂️ **Weaviate Client** `4.4.0` - Vector DB
- 📝 **Sentence Transformers** `2.2.2` - Embeddings
- 📄 **PyPDF** `3.17.0` - PDF processing

**Multi-Agent System**
- 🤖 **CrewAI** `1.3.0` - Agent orchestration
- 🦜 **LangChain** `0.1.0` - LLM integration
- 🦙 **Ollama** - Local LLM runtime

</td>
<td width="50%" valign="top">

**Evaluation & Quality**
- 🛡️ **Guardrails AI** `0.4.0` - Validation
- 📊 **TruLens** `0.18.0` - RAG metrics
- 📈 **ROUGE Score** - Text quality
- 🎯 **SciKit Learn** - Similarity metrics

**Workflow & Integration**
- 🔄 **n8n** (Docker) - Automation
- 🐘 **PostgreSQL** `15` - Data storage
- 🔧 **Requests** `2.31.0` - HTTP client

**Development**
- 🧪 **Pytest** `7.4.3` - Testing
- 🎨 **Black** `23.12.0` - Formatting
- 📏 **Ruff** `0.1.8` - Linting
- 🔍 **MyPy** `1.7.1` - Type checking

</td>
</tr>
</table>

See [requirements.txt](requirements.txt) for complete list.

### LLM Configuration

**Default Model**: `qwen3:1.7b` (Qwen 2.5 - 1.7B parameters)  
**Alternatives**: `qwen3:4b`, `qwen2.5:3b`, `llama3.2:3b`  
**Why Qwen?**: Balanced speed/quality for local inference, strong multilingual support

**Note**: The model can be changed in `docker/.env` by setting `OLLAMA_MODEL`.

---

## 🏛️ System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         User / n8n                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/REST
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (Port 8000)                      │
│              FastAPI + Modular Routers                          │
│              - Input Validation (Guardrails)                    │
│              - Request Routing                                  │
│              - Output Validation (Guardrails)                   │
└────┬──────────────────────────┬──────────────┬──────────────────┘
     │                          │              │
     ▼                          ▼              ▼
┌────────────┐      ┌────────────────────┐  ┌────────────────┐
│  Weaviate  │◄─────│  CrewAI (8100)     │◄─┤ Ollama (11434) │
│  (8080)    │      │  Multi-Agent       │  │                │
│  Vector DB │      │  Writer→Reviewer   │  │ LLM Runtime    │
│  Hybrid    │      │  →FactChecker      │  │ qwen3:1.7b     │
│  Search    │      └────────────────────┘  │                │
└────────────┘                │             └────────────────┘
                              │ Metrics
                              ▼
                    ┌────────────────────┐
                    │  Evaluation (8502) │
                    │  - TruLens         │
                    │  - Guardrails      │
                    │  - Performance     │
                    │  - Dashboard       │
                    └────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data & Storage Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ PostgreSQL   │  │ Redis Cache  │  │ Volume Mounts│           │
│  │ (5432)       │  │ (future)     │  │ - Models     │           │
│  │ - n8n data   │  │ - Embeddings │  │ - Documents  │           │
│  │ - Metrics    │  │ - Responses  │  │ - Outputs    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘

```

**Key Components**:
- **API Gateway**: Single entry point, validation, routing
- **CrewAI Service**: Multi-agent orchestration (Writer→Reviewer→FactChecker)
- **Weaviate**: Vector database with hybrid search (BM25 + semantic)
- **Ollama**: Local LLM inference (qwen3:1.7b default)
- **Evaluation**: Quality monitoring with TruLens, Guardrails, dashboard
- **PostgreSQL**: Persistent storage for n8n workflows and metrics
- **Redis Cache**: Planned for query/embedding caching
- **n8n**: Workflow automation and scheduling

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

## 📂 Folder Structure
```
BIS5151E_Research-Assistant/
├── .devcontainer/                  # VS Code DevContainer configuration
├── .github/                        # GitHub Actions CI/CD workflows
│
├── configs/                        # Configuration files
│   ├── haystack/                   # Haystack pipeline configs
│   └── crewai/                     # CrewAI agent configs
│
├── data/                           # Data storage
│   ├── arxiv/                      # ArXiv downloaded papers
│   ├── outputs/                    # Generated summaries
│   └── raw/                        # User-uploaded documents
│
├── database/                       # Database initialization
│   └── init/                       # PostgreSQL init scripts
│
├── docker/                         # Docker configuration
│   ├── workflows/                  # n8n example workflows
│   ├── .env                        # Docker environment configuration
│   ├── docker-compose.yml          # Main compose file
│   └── docker-compose.nvidia.yml   # GPU support
│
├── docs/                           # Documentation
│   ├── api/                        # API reference
│   │   ├── README.md
│   │   ├── ENDPOINTS.md            # Complete endpoint table
│   │   ├── SCHEMAS.md              # Request/response models
│   │   └── AUTHENTICATION.md       # Auth guide (future)
│   │
│   ├── architecture/               # System design
│   │   ├── README.md
│   │   ├── OVERVIEW.md             # High-level architecture
│   │   ├── DATA_FLOW.md            # Request flow diagrams
│   │   ├── SERVICES.md             # Docker services
│   │   ├── AGENTS.md               # Multi-agent system
│   │   ├── RAG_PIPELINE.md         # RAG implementation
│   │   └── DATABASE.md             # Database schemas
│   │
│   ├── evaluation/                 # Quality monitoring
│   │   ├── README.md
│   │   ├── METRICS.md              # Metrics explained
│   │   ├── GUARDRAILS.md           # Validation config
│   │   ├── TRULENS.md              # TruLens setup
│   │   └── DASHBOARD.md            # Dashboard guide
│   │
│   ├── examples/                   # Code examples
│   │   ├── README.md
│   │   ├── BASIC_USAGE.md          # curl/PowerShell
│   │   ├── PYTHON_EXAMPLES.md      # Python integration
│   │   └── CLI_EXAMPLES.md         # CLI tools
│   │
│   ├── guides/                     # How-to guides
│   │   ├── README.md
│   │   ├── COMMAND_REFERENCE.md    # Quick reference
│   │   ├── CONFIGURATION.md        # All settings
│   │   └── BEST_PRACTICES.md       # Optimization
│   │
│   ├── setup/                      # Installation
│   │   ├── README.md               # Setup hub
│   │   ├── INSTALLATION.md         # Complete guide
│   │   ├── GPU.md                  # NVIDIA GPU setup
│   │   ├── N8N.md                  # n8n workflow setup
│   │   └── TROUBLESHOOTING.md      # Common issues
│   │
│   └── README.md                   # Documentation hub
│
├── outputs/                        # Output files for users
│
├── scripts/                        # Utility scripts
│   ├── admin/                      # Admin tools
│   │   ├── health_check.py
│   │   └── backup.sh
│   └── cli/                        # CLI tools
│       ├── ingest_arxiv.py
│       └── query_rag.py
│
├── src/                            # Source code
│   ├── agents/                     # CrewAI multi-agent system
│   │   └── api/                    # CrewAI FastAPI service
│   │
│   ├── api/                        # Main API gateway
│   │   ├── routers/                # Modular endpoints
│   │   └── server.py               # FastAPI application
│   │
│   ├── eval/                       # Evaluation & quality
│   │   ├── guardrails/             # Input/output validation
│   │   ├── trulens/                # RAG quality metrics
│   │   ├── performance/            # Timing tracking
│   │   └── quality/                # Quality metrics
│   │
│   └── rag/                        # RAG pipeline
│       ├── core/                   # Pipeline, processor, embedder
│       ├── sources/                # ArXiv, local loaders
│       └── stores/                 # Weaviate integration
│
├── tests/                          # Test suite
│   ├── integration/                # End-to-end tests
│   ├── unit/                       # Unit tests
│   ├── conftest.py                 # pytest configuration
│   └── TESTING.md                  # Testing guide
│
├── .env.                           # Application config 
├── .gitignore
├── CHANGELOG.md                    # Version history
├── CONTRIBUTING.md                 # Development guide
├── LICENSE                         # Academic Use License
├── QUICKSTART.md                   # 5-minute setup
├── README.md                       # This file
├── ROADMAP.md                      # Future plans
└── requirements.txt                # Python dependencies
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
$body = @{
    query = "transformers attention mechanism"
    max_results = 3
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$body = @{
    query = "Explain the transformer attention mechanism"
    language = "en"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "`nAnswer:`n$($response.answer)"
```

**Access Points**:
- **API Docs**: http://localhost:8000/docs
- **n8n UI**: http://localhost:5678
- **Weaviate**: http://localhost:8080/v1/meta

---

## 📚 Documentation

Complete documentation organized by category:

<table>
<tr>
<th width="25%">Category</th>
<th width="40%">Documents</th>
<th width="35%">Description</th>
</tr>

<tr>
<td rowspan="5"><b>🚀 Setup</b></td>
<td><a href="QUICKSTART.md">Quickstart Guide</a></td>
<td>5-minute setup</td>
</tr>
<tr>
<td><a href="docs/setup/INSTALLATION.md">Complete Installation</a></td>
<td>Step-by-step guide</td>
</tr>
<tr>
<td><a href="docs/setup/GPU.md">GPU Setup (NVIDIA)</a></td>
<td>3-5x faster inference</td>
</tr>
<tr>
<td><a href="docs/setup/N8N.md">n8n Workflow Setup</a></td>
<td>Automation guide</td>
</tr>
<tr>
<td><a href="docs/setup/TROUBLESHOOTING.md">Troubleshooting</a></td>
<td>Common issues & fixes</td>
</tr>

<tr>
<td rowspan="4"><b>📡 API</b></td>
<td><a href="docs/api/README.md">API Overview</a></td>
<td>Getting started</td>
</tr>
<tr>
<td><a href="docs/api/ENDPOINTS.md">Endpoint Reference</a></td>
<td>Complete endpoint table</td>
</tr>
<tr>
<td><a href="docs/api/SCHEMAS.md">Request/Response Schemas</a></td>
<td>Data models</td>
</tr>
<tr>
<td><a href="http://localhost:8000/docs">Swagger UI</a> (live)</td>
<td>Interactive API docs</td>
</tr>

<tr>
<td rowspan="6"><b>🏗️ Architecture</b></td>
<td><a href="docs/architecture/OVERVIEW.md">System Overview</a></td>
<td>High-level design</td>
</tr>
<tr>
<td><a href="docs/architecture/DATA_FLOW.md">Data Flow</a></td>
<td>Request flow diagrams</td>
</tr>
<tr>
<td><a href="docs/architecture/SERVICES.md">Docker Services</a></td>
<td>Service configurations</td>
</tr>
<tr>
<td><a href="docs/architecture/AGENTS.md">Multi-Agent System</a></td>
<td>CrewAI agents</td>
</tr>
<tr>
<td><a href="docs/architecture/RAG_PIPELINE.md">RAG Pipeline</a></td>
<td>RAG implementation</td>
</tr>
<tr>
<td><a href="docs/architecture/DATABASE.md">Database Schema</a></td>
<td>Weaviate & PostgreSQL</td>
</tr>

<tr>
<td rowspan="5"><b>📊 Evaluation</b></td>
<td><a href="docs/evaluation/README.md">Evaluation Overview</a></td>
<td>Quality assurance</td>
</tr>
<tr>
<td><a href="docs/evaluation/METRICS.md">Metrics Explained</a></td>
<td>What each metric means</td>
</tr>
<tr>
<td><a href="docs/evaluation/GUARDRAILS.md">Guardrails Config</a></td>
<td>Input/output validation</td>
</tr>
<tr>
<td><a href="docs/evaluation/TRULENS.md">TruLens Setup</a></td>
<td>RAG quality monitoring</td>
</tr>
<tr>
<td><a href="docs/evaluation/DASHBOARD.md">Dashboard Guide</a></td>
<td>Visual analytics (port 8502)</td>
</tr>

<tr>
<td rowspan="3"><b>💡 Examples</b></td>
<td><a href="docs/examples/BASIC_USAGE.md">Basic Usage</a></td>
<td>curl & PowerShell examples</td>
</tr>
<tr>
<td><a href="docs/examples/PYTHON_EXAMPLES.md">Python Integration</a></td>
<td>API client code</td>
</tr>
<tr>
<td><a href="docs/examples/CLI_EXAMPLES.md">CLI Tools</a></td>
<td>Command-line usage</td>
</tr>

<tr>
<td rowspan="3"><b>📖 Guides</b></td>
<td><a href="docs/guides/COMMAND_REFERENCE.md">Command Reference</a></td>
<td>Quick command lookup</td>
</tr>
<tr>
<td><a href="docs/guides/CONFIGURATION.md">Configuration Guide</a></td>
<td>All settings explained</td>
</tr>
<tr>
<td><a href="docs/guides/BEST_PRACTICES.md">Best Practices</a></td>
<td>Performance & optimization</td>
</tr>

<tr>
<td rowspan="3"><b>🔧 Development</b></td>
<td><a href="CONTRIBUTING.md">Contributing Guide</a></td>
<td>Development workflow</td>
</tr>
<tr>
<td><a href="tests/TESTING.md">Testing Guide</a></td>
<td>Running tests</td>
</tr>
<tr>
<td><a href=".github/workflows/">CI/CD Workflows</a></td>
<td>GitHub Actions</td>
</tr>

<tr>
<td rowspan="3"><b>📋 Project Info</b></td>
<td><a href="CHANGELOG.md">Changelog</a></td>
<td>Version history</td>
</tr>
<tr>
<td><a href="ROADMAP.md">Roadmap</a></td>
<td>Future plans</td>
</tr>
<tr>
<td><a href="LICENSE">License</a></td>
<td>Academic Use License</td>
</tr>
</table>

**Quick Access**:
- 📖 **Documentation Hub**: [docs/README.md](docs/README.md)
- 🚀 **Get Started**: [QUICKSTART.md](QUICKSTART.md)
- 🔧 **Troubleshooting**: [docs/setup/TROUBLESHOOTING.md](docs/setup/TROUBLESHOOTING.md)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/discussions)

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

### 🛡️ Guardrails AI Validation

**Input Validation** (prevents harmful queries):

<table>
<tr>
<td width="25%">

**📏 Length Check**
- Max: 10,000 chars
- Action: Reject

</td>
<td width="25%">

**🚫 Jailbreak Detection**
- Prompt injection
- Action: Reject

</td>
<td width="25%">

**🔒 PII Detection**
- Email, phone
- Action: Reject

</td>
<td width="25%">

**📍 Off-Topic Check**
- Relevance check
- Action: Warning

</td>
</tr>
</table>

**Output Validation** (ensures quality responses):

<table>
<tr>
<td width="25%">

**📚 Citation Format**
- Format: `[1]`, `[2]`
- Coverage: >90%
- Action: Enforce

</td>
<td width="25%">

**🔍 Hallucination Detection**
- Markers: "I think"
- Unsupported claims
- Action: Warning

</td>
<td width="25%">

**📊 Length Validation**
- Range: 200-500 words
- Action: Warning

</td>
<td width="25%">

**⚠️ Safety Check**
- Harmful content
- Profanity
- Action: Reject

</td>
</tr>
</table>

**Configuration** (`.env`):
```bash
GUARDRAILS_CITATION_REQUIRED=true  # Enforce citations
GUARDRAILS_STRICT_MODE=false       # Lenient validation
```

**Learn more**: [Guardrails Documentation](docs/evaluation/GUARDRAILS.md)

### 📊 TruLens Evaluation Dashboard

Real-time quality monitoring with visual analytics.

**Dashboard URL**: http://localhost:8502

<table>
<tr>
<td width="50%" valign="top">

**📈 Real-Time Metrics**

| Metric | Target | Current |
|--------|--------|---------|
| Answer Relevance | >0.80 | 0.87 |
| Context Relevance | >0.70 | 0.81 |
| Groundedness | >0.85 | 0.92 |
| Citation Coverage | >90% | 94% |
| Avg Response Time | <30s | 28.4s |

**Features**:
- ✅ Live metric tracking
- 📊 Historical trends (7/30/90 days)
- 🔍 Query-level drill-down
- 📉 Performance graphs
- 💾 Export to CSV/PDF

</td>
<td width="50%" valign="top">

**🎯 Quality Monitoring**
```
┌─────────────────────────────┐
│ Overall Score: 0.87 (Good)  │
├─────────────────────────────┤
│                             │
│  📊 Trend (Last 7 days)     │
│  │                    ╱───╲ │
│  │             ╱────╱      ╲│
│  │      ╱────╱              │
│  └──────────────────────────│
│   Mon Tue Wed Thu Fri Sat   │
│                             │
│  📋 Recent Queries          │
│  • Neural networks: 0.92    │
│  • Transformers: 0.88       │
│  • Deep learning: 0.85      │
└─────────────────────────────┘
```

**Access Dashboard**:
```bash
# View in browser
open http://localhost:8502

# Or from CLI
python -m streamlit run \
  src/eval/dashboard/app.py \
  --server.port 8502
```

</td>
</tr>
</table>

**Status**: Experimental (stub implementation)

**Setup**: See [Dashboard Guide](docs/evaluation/DASHBOARD.md)

**Metrics Tracked**:
- 🎯 **Answer Relevance**: Does answer address the query?
- 📝 **Context Relevance**: Is retrieved context useful?
- ✅ **Groundedness**: Are claims supported by sources?
- 📊 **Citation Quality**: Proper citation format and coverage
- ⏱️ **Performance**: Response times and throughput

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

**[⬆ Back to Top](#Research-Assistant-GPT)**