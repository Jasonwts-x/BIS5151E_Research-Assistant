# Project: ResearchAssistantGPT - Step [F] Implementation

You are my coding and architecture design assistant for my GENERATIVE AI (RAG + AGENTIC AI) project.

## Project Context

I'm building **ResearchAssistantGPT** for the BIS5151E course at Hochschule Pforzheim. This is a RAG-based research assistant with multi-agent workflows orchestrated by n8n.

**Project Documents Available in Context:**
- `Research-Assistant_COMPRESSED_CONTEXT_GEM.txt` - Project overview and architecture
- `Research-Assistant_IMPLEMENTATION_PLAN.txt` - Detailed implementation roadmap (Steps A-H)
- GitHub Repository: All source code files are available in the project context

**Please read these documents before starting.**

---

## Current Status

**Completed Steps:**
- ✅ Step A: DevContainer as compose service
- ✅ Step B: API service (FastAPI gateway, port 8000)
- ✅ Step C: Ollama service (LLM runtime, port 11434)
- ✅ Step D: CrewAI integration (multi-agent service, port 8100)
- ✅ Step E: Rag Rework (implemented; but still testing; a few errors present)

**Current Step: [STEP F - Trulens & Guardrails]**

**Goal:** [Implement Trulens and Guardrails.]

---

## Tech Stack

**Services (Docker Compose):**
- `postgres:15` - n8n database (port 5432)
- `weaviate:latest` - Vector database (port 8080)
- `ollama:latest` - LLM runtime (port 11434)
- `n8n:latest` - Workflow orchestrator (port 5678)
- `api` - Main API gateway (port 8000, target: api)
- `crew` - CrewAI service (port 8100, target: crew)
- `devcontainer` - Development environment (target: dev)

**Python Stack:**
- Python 3.11
- FastAPI + Uvicorn
- Haystack 2.x + Weaviate integration
- CrewAI 1.3.0 + LangChain-Ollama
- Ollama (qwen3:4b model)
- Sentence-transformers for embeddings

**Key Architecture:**
```
n8n (orchestrator)
  ↓
API Gateway (8000) → RAG Service
  ↓                → Ollama (11434)
Crew Service (8100) → Weaviate (8080)
```

---

## Project Structure
```
src/
  agents/           # CrewAI implementation (Step D)
    api/            # Crew service API layer
    roles/          # Agent definitions
    tasks/          # Task definitions
    crews/          # Crew compositions
    runner.py       # Execution logic
  api/              # Main API gateway
    routers/        # Endpoint implementations
    schemas/        # Pydantic models
    server.py       # Main FastAPI app
  rag/              # RAG pipeline (Haystack + Weaviate)
    core/
    ingestions/
    sources/
  eval/             # Evaluation (TruLens, Guardrails - future)
  utils/            # Configuration and utilities
```

---

## Coding Standards & Preferences

**Code Style:**
- Use type hints everywhere
- Follow PEP 8 (via ruff + black)
- Imports: `from __future__ import annotations`
- Use logging, not print statements
- Comprehensive docstrings

**Architecture Preferences:**
- Clean separation of concerns
- Microservices pattern (separate Docker services)
- Gateway pattern (API → Crew service)
- Shared schemas (single source of truth)
- Environment variable configuration

**File Organization:**
- `__init__.py` files with explicit imports + `__all__`
- Minimal server.py files (just FastAPI app + router includes)
- Business logic in separate modules (not in routers)

**Commit Style:**
- Thematic grouping (not file-by-file)
- Conventional commits: `category: description`
- Categories: deps, agents, api, docker, tests, docs, refactor
- Present tense: "add", "implement", "update"

---

## Workflow Process

**For each implementation step:**
1. Read the implementation plan for the current step
2. Discuss architecture and design decisions
3. Generate all required code files
4. Provide organized commit groups
5. Test and verify

**After each step:**
- Run formatters: `ruff check --fix` + `black`
- Run tests: `pytest`
- Build and test Docker services
- Commit changes in logical groups
- Push to GitHub

---

## Current Task

- Implement Trulens
- Implement Guardrails
- Configure Both

**Deliverables:**
- Short description of your findings
- Explanation of your target goal for this task
- Description of the plan
- Concrete steps for implementation
- Clear code and instruction for each file I have do add, delete or update

**Success Criteria:**
Complete, connected and working rag and weaviate integration.

---

## Questions?

I'm ready to start implementing Step [F]. Do you have any questions about the project context, architecture, or what we need to do?