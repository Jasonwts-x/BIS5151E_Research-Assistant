# ResearchAssistantGPT

[![CI Pipeline](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-Academic-green.svg)](LICENSE)

> **AI-powered research assistant** with RAG and multi-agent workflows for academic literature review

---

## 🎯 Overview

ResearchAssistantGPT is a **RAG-based research assistant** that generates **cited summaries** from academic papers using multi-agent AI workflows. Built for the BIS5151 course at Hochschule Pforzheim.

**Key Features:**
- 📚 Automatic ArXiv paper ingestion
- 🔍 Hybrid search (BM25 + semantic)
- 🤖 Multi-agent workflow (Writer → Reviewer → FactChecker)
- ✅ Citation validation & fact-checking
- 🌐 Multilingual support (EN, DE, FR, ES)
- 🔒 Privacy-preserving (local deployment)

---

## 🚀 Quick Start

**Prerequisites:** Docker Desktop (16GB+ RAM), Git, 20GB disk space

### 1. Clone & Configure
```bash
git clone https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git
cd BIS5151E_Research-Assistant

# Copy environment files
cp .env.example .env
cp docker/.env.example docker/.env

# Edit docker/.env: Set POSTGRES_PASSWORD and N8N_ENCRYPTION_KEY
```

### 2. Start Services
```bash
docker compose -f docker/docker-compose.yml up -d
```

### 3. Verify Installation
```bash
python scripts/admin/health_check.py
```

### 4. First Query
```bash
curl -X POST http://localhost:8000/rag/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "max_results": 3}'

curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "language": "en"}'
```

**🎉 Done!** See [QUICKSTART.md](QUICKSTART.md) for detailed guide.

---

## 📚 Documentation

| Resource | Description |
|----------|-------------|
| [**Quickstart Guide**](QUICKSTART.md) | Step-by-step installation |
| [**API Reference**](docs/api/README.md) | Complete API documentation |
| [**Architecture**](docs/architecture/README.md) | System design & components |
| [**Examples**](docs/examples/README.md) | Usage examples & workflows |
| [**Troubleshooting**](docs/troubleshooting/README.md) | Common issues & solutions |
| [**Contributing**](CONTRIBUTING.md) | How to contribute |
| [**Roadmap**](ROADMAP.md) | Future features |

**Quick Links:**
- API Docs (Swagger): http://localhost:8000/docs
- n8n Workflow UI: http://localhost:5678
- Weaviate Console: http://localhost:8080/v1/meta

---

## 🏗️ Architecture
```
User/n8n → API Gateway → CrewAI Service → RAG Pipeline → Weaviate
                              ↓
                           Ollama LLM
```

**Components:**
- **RAG Pipeline**: Document ingestion, chunking, hybrid retrieval
- **CrewAI Agents**: Writer (drafts), Reviewer (edits), FactChecker (validates)
- **Weaviate**: Vector database for semantic search
- **Ollama**: Local LLM inference (qwen2.5:3b)
- **n8n**: Workflow automation & orchestration

See [Architecture Documentation](docs/architecture/README.md) for details.

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

# Unit only (fast)
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality
```bash
ruff check src tests --fix  # Lint
black src tests             # Format
mypy src                    # Type check
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development guide.

---

## 📊 Tech Stack

| Category | Technology |
|----------|-----------|
| **Language** | Python 3.11 |
| **RAG** | Haystack 2.x, Weaviate |
| **Embeddings** | sentence-transformers |
| **LLM** | Ollama (qwen2.5:3b) |
| **Agents** | CrewAI |
| **API** | FastAPI |
| **Orchestration** | n8n |
| **Testing** | pytest, pytest-cov |
| **Linting** | ruff, black, mypy |
| **Containers** | Docker, Docker Compose |

---

## 🎓 Course Context

**Course:** BIS5151 – Generative Artificial Intelligence  
**Institution:** Hochschule Pforzheim  
**Program:** Master of Information Systems  
**Semester:** Winter 2025/26  
**Instructor:** Prof. Dr. Manuel Fritz, MBA

---

## 👥 Team

| Name | Role | GitHub |
|------|------|--------|
| Jason Warzecha | Project Lead | [@Jasonwts-x](https://github.com/Jasonwts-x) |
| [Team Member 2] | RAG Engineer | [@username](https://github.com/username) |
| [Team Member 3] | Agent Developer | [@username](https://github.com/username) |
| [Team Member 4] | Integration Lead | [@username](https://github.com/username) |

---

## 📄 License

Academic use only. See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Coding standards
- Testing requirements
- Pull request process

---

## 🆘 Support

- **Issues:** [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/discussions)
- **Documentation:** [docs/](docs/)

---

**Made with ❤️ for BIS5151 @ Hochschule Pforzheim**