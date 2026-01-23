# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Multi-agent CrewAI workflow (Writer → Reviewer → FactChecker)
- RAG pipeline with Weaviate hybrid search
- ArXiv paper ingestion
- Guardrails safety checks
- TruLens monitoring support

### Changed
- Refactored ingestion to separate concerns
- Improved error handling in API
- Updated documentation structure

### Fixed
- Weaviate URL parsing issues
- Resource cleanup in pipeline
- ArXiv network access from containers

## [0.2.0] - 2025-01-15

### Added
- CrewAI service as separate container
- API gateway proxy pattern
- Comprehensive testing suite

## [0.1.0] - 2025-01-01

### Added
- Initial RAG pipeline
- Weaviate integration
- Ollama LLM support
- Basic API endpoints