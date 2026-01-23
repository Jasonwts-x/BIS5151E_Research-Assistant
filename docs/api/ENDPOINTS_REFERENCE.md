# Complete Endpoints Reference

Quick reference for all API endpoints.

## System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness check |
| GET | `/version` | Version info |
| GET | `/ready` | Readiness check |

## RAG

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rag/query` | Query with multi-agent processing |
| POST | `/rag/ingest/local` | Ingest local files |
| POST | `/rag/ingest/arxiv` | Fetch & ingest ArXiv papers |
| GET | `/rag/stats` | Index statistics |
| DELETE | `/rag/admin/reset-index` | Clear all documents |

## Ollama

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ollama/info` | Service info & models |
| GET | `/ollama/models` | List models |
| POST | `/ollama/chat` | Direct LLM chat |

## CrewAI

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/crewai/run` | Execute workflow |
| GET | `/crewai/status/{job_id}` | Job status (not implemented) |

---

**[⬆ Back to API Docs](README.md)**