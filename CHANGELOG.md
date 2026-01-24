# Changelog

All notable changes to ResearchAssistantGPT are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Multi-agent CrewAI workflow (Writer → Reviewer → FactChecker)
- Hybrid RAG pipeline with Weaviate vector database
- ArXiv paper ingestion with automatic metadata extraction
- Local file ingestion (PDF, TXT) with deduplication
- Guardrails safety checks for harmful content (experimental)
- TruLens monitoring integration (stub implementation)
- Multilingual support (EN, DE, FR, ES)
- Comprehensive test suite (unit + integration)
- n8n workflow automation examples
- GPU support configuration (NVIDIA and AMD)
- CLI tools for ingestion and querying
- Health check and monitoring scripts
- Organized documentation structure
- GitHub Actions CI/CD pipeline
- Docker Compose orchestration with profiles
- Development helper scripts
- API endpoint for statistics
- Deterministic chunk IDs for deduplication
- Citation format validation

### Changed
- Refactored ingestion engine into modular components
- Improved error handling across all API endpoints
- Migrated test structure to unit/integration organization
- Enhanced RAG pipeline with singleton pattern
- Updated Weaviate schema with explicit class definitions
- Improved logging throughout application
- Restructured documentation for better navigation
- Separated ArXiv downloads into dedicated directory

### Fixed
- Weaviate URL parsing issues in Docker environment
- Resource cleanup in pipeline shutdown
- ArXiv network access from Docker containers
- Duplicate document handling in ingestion
- Memory leaks in embedding generation
- Race conditions in concurrent queries
- Container startup dependency ordering

### Security
- Added input validation for all API endpoints
- Implemented query length limits (10,000 chars)
- Added content safety checks via Guardrails
- Sanitized file paths in ingestion

### Documentation
- Complete API reference with examples
- Architecture diagrams and design docs
- Troubleshooting guides
- n8n workflow examples
- Development setup guide
- Testing documentation
- Contribution guidelines

---

## [0.3.0] - 2025-01-20

### Added
- ArXiv source integration with metadata
- Multi-language support (EN, DE, FR, ES)
- FactChecker agent for citation validation
- Translation capabilities (experimental)
- Hybrid retrieval (BM25 + vector)

### Changed
- Upgraded to Weaviate 1.23
- Switched to Ollama for LLM inference (qwen2.5:3b)
- Improved chunk size optimization (500 chars)

### Fixed
- Memory leaks in embedding generation
- Race conditions in concurrent queries
- Timeout issues with large documents

### Removed
- HuggingFace Hub dependency (moved to local Ollama)

---

## [0.2.0] - 2025-01-15

### Added
- CrewAI multi-agent system
- API gateway with proxy pattern
- Docker Compose orchestration
- n8n integration
- PostgreSQL for n8n persistence
- Health check endpoints

### Changed
- Separated CrewAI into dedicated service
- Refactored API into modular routers
- Improved container networking

### Fixed
- Container startup dependencies
- Network isolation issues
- Environment variable handling

---

## [0.1.0] - 2025-01-01

### Added
- Initial RAG pipeline with Haystack
- Weaviate integration
- Ollama LLM support
- Basic FastAPI server
- Local file ingestion
- Query endpoint with top-k retrieval
- Docker support
- Basic documentation

---

## Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR version** (X.0.0): Breaking API changes
- **MINOR version** (0.X.0): New features (backward-compatible)
- **PATCH version** (0.0.X): Bug fixes

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute and update this changelog.

---

## Links

- [GitHub Releases](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/releases)
- [Project Roadmap](ROADMAP.md)
- [Documentation](docs/)