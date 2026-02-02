---

## [0.3.0] - 2025-01-20

### Added
- ArXiv source integration with metadata extraction
- Multi-language support (EN, DE, FR, ES)
- FactChecker agent for citation validation
- Translation capabilities (experimental)
- Hybrid retrieval (BM25 + vector search)

### Changed
- Upgraded to Weaviate 1.23.0
- Switched to Ollama for LLM inference (qwen3:4b)
- Improved chunk size optimization (500 → 350 characters)

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

- **GitHub Repository**: https://github.com/Jasonwts-x/BIS5151E_Research-Assistant
- **GitHub Releases**: https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/releases
- **Project Roadmap**: [ROADMAP.md](ROADMAP.md)
- **Documentation Hub**: [docs/README.md](docs/README.md)
- **API Reference**: [docs/api/ENDPOINTS.md](docs/api/ENDPOINTS.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Current Version**: 1.0.0  
**Last Updated**: February 2, 2025