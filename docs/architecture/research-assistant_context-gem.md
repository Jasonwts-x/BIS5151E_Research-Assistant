COMPRESSED CONTEXT GEM â€” BIS5151E_Research-Assistant

Project Goal (Big Picture)
- Build a â€œResearchAssistantGPTâ€ stack for BIS5151: RAG-based research assistant with:
  - ingestion of local docs/articles,
  - vector search + hybrid retrieval,
  - LLM-based answering/summarization,
  - agentic workflows (CrewAI) + orchestration via n8n,
  - later: evaluation/guardrails (TruLens + Guardrails), optional translation add-on (DeepL).
- Strong preference: run as much as sensible INSIDE Docker Compose as services on one network.

Tech Stack & Environment
- Host: Windows + PowerShell, Docker Desktop, Docker Compose.
- Dev: VS Code (Dev Containers), but now also a dedicated â€œdevcontainerâ€ service in docker-compose.
- Core services (compose): postgres:15, weaviate:latest, olama_latest, n8n:latest, devcontainer (Python 3.11 base image).
- Python libs: Haystack 2.x, weaviate-haystack, sentence-transformers, requests, pytest, ruff/black; fastapi present (API step next).
- Weaviate is configured as â€œno vectorizerâ€ (we generate embeddings in Python).
- We chose qwen3:4b as our llm, running inside ollama.

Architecture Overview (Current)
- docker/docker-compose.yml runs: Postgres (n8n DB), Weaviate (vector store), n8n (orchestrator UI/flows), devcontainer (workspace + dev tooling).
- All services share a compose network (research_net) and named volumes for persistence.
- Repo structure (high level):
  - src/agents/â€¦ : agents.py (one for each agents) and orchestrator.py (will change with CrewAI Integration)
  - src/app/â€¦ : api.py, main.py, server.py (main app, and api service; will probably change with next steps)
  - src/eval/â€¦ : guardrails and trulens
  - src/rag/â€¦ : RAG pipeline (Haystack + Weaviate docstore + embedding + hybrid retriever)
  - tests/â€¦ : pytest smoke/integration-ish tests
  - docker/â€¦ : compose file, env, n8n workflows folder
  - .devcontainer/â€¦ : devcontainer.json + Dockerfile

Core Project Logic (Big Picture)
- RAG:
  - Documents are chunked + embedded with sentence-transformers.
  - Stored in Weaviate; retrieval uses hybrid retrieval (lexical + vector) requiring query + query_embedding.
  - Pipeline exposes a â€œrun(query, top_k)â€ returning relevant chunks.
- Orchestration (target design):
  - n8n is the outer orchestrator (triggers, schedules, UI, flow logic).
  - API service (planned) exposes endpoints for â€œingestâ€, â€œqueryâ€, â€œstatusâ€ so n8n can call them.
  - CrewAI (planned) handles multi-agent reasoning/roles; n8n triggers a CrewAI-run via API or worker service; n8n remains orchestration layer.
- Quality later:
  - deterministic ingestion + locked Weaviate schema + CLI entrypoint + one-command demo docs.
  - TruLens + Guardrails after baseline workflow is stable.
  - DeepL only if time remains.

Project Plan Moving Forward (Agreed Order)
A) Devcontainer as a compose service (Done)
B) Add API service in compose (FastAPI) to expose RAG operations to n8n
C) Add  Ollama service in compose (needed later for agent/LLM work)
D) Add CrewAI in compose (as its own service/container; integrate with n8n orchestration)
E) Optimize core RAG: lock schema, deterministic ingestion, CLI entrypoint, one-command demo docs
F) Add TruLens + Guardrails
G) QoL + optional CI + cleanup
H) Optional DeepL add-on

-> You find the detailed implementation plan in another document in our Project context.

Completed Milestones (High-Level)
- Base Docker stack works: Postgres + Weaviate + n8n start successfully and are reachable on localhost.
- RAG pipeline exists and is tested via pytest; earlier embedder API mismatch was fixed and pipeline retrieval now works.
- We introduced â€œstep-by-step implementation plan Aâ€“Hâ€ and a strict workflow: finish a step â†’ verify clean â†’ commit/push.
- We completed step A, B and C.

Current Task (Step D)
- Implement crewai logic src/crew folder
- Implemented API Connections for crewai (including router/schemas if needed)
- Verifying the CrewAI service and connection Setup.


Style, Coding Rules, and Process Preferences
- Work one step at a time in order Aâ†’H.
- After each step:
  1) verify everything works (docker compose up, healthchecks, smoke checks),
  2) run ruff + black + pytest,
  3) prepare commit packages; with  packages ordered in commit order.
	> thematic grouping; considering which files belong together and where modified together.
	> give the groups as commands:
		> git add with files for the group, 
		> git commit with message for the group (message with out chore or similar, instead env:/rag:/etc.) 
  4) commit + push to GitHub.
- Prefer clean compose structure and consistent ordering (name â†’ services â†’ networks â†’ volumes; within service: identity â†’ reliability â†’ connectivity â†’ env â†’ storage â†’ constraints).
- When working on files give me either the complete improved files or the necessary code snippets as code inside your answer.


ARCHIVE INSTRUCTION FOR NEW CHAT
- Consider the files provided via the GitHub repo.