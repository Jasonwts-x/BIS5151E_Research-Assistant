# ResearchAssistantGPT

This project is part of the BIS5151 Generative Artificial Intelligence course at Hochschule Pforzheim.

---

## 🎓 Course Context & Team
**Course:** BIS5151 – Generative Artificial Intelligence  
**Lecturer:** Prof. Dr. Manuel Fritz, MBA  
**Semester:** Winter 2025/26 – Hochschule Pforzheim  

**Project Group:** ResearchAssistantGPT  
**Members:** Dilsat Bekil, Karim Epple, Jason Waschtschenko, Rigon Rexha, Eren Kaya  

---

## 🧠 Project Overview
**ResearchAssistantGPT** is a local, privacy-preserving research assistant designed to summarize academic papers and verify all factual claims using citations from a connected document corpus.

The tool demonstrates how **Retrieval-Augmented Generation (RAG)**, **multi-agent collaboration**, and **AI governance** can work together to create trustworthy generative systems.

---

## 🧩 Core Objectives
1. Retrieve academic literature (PDFs, articles, etc.) using a **Haystack** pipeline.  
2. Generate concise, 300-word summaries with **Ollama** running a local LLM.  
3. Verify all statements through **FactChecker** agents and output traceability tables.  
4. Evaluate reliability using **TruLens** and enforce formatting/policy via **Guardrails AI**.  

---

## ⚙️ Technical Stack
| Category | Tool | Purpose |
|-----------|------|----------|
| **IDE** | Visual Studio Code | Development environment |
| **Language** | Python 3.11+ | Core programming |
| **Containerization** | Docker Desktop | Reproducibility & orchestration |
| **Automation** | n8n | Connect all workflow components |
| **RAG Framework** | Haystack | Document indexing and retrieval |
| **LLM Runtime** | Ollama (Llama 3) | Local inference |
| **Agents** | CrewAI | Writer, Reviewer, FactChecker |
| **Evaluation** | TruLens + Guardrails | Quality & compliance checks |

---

## 📁 Folder Structure
BIS5151E_Research-Assistant/
├─ .vscode/ → VS Code configuration
├─ configs/ → app.yaml, model and pipeline settings
├─ data/ → raw PDFs, processed chunks, external corpora
├─ docker/ → docker-compose.yml and container configs
├─ outputs/ → generated summaries & citation trace tables
├─ scripts/ → helper scripts (PDF importers, converters)
├─ src/ → main codebase
│ ├─ app/ → entrypoints and orchestration scripts
│ ├─ rag/ → Haystack ingestion and query logic
│ ├─ agents/ → multi-agent definitions (CrewAI)
│ └─ eval/ → evaluation & governance components
└─ tests/ → unit/integration tests

---

## 🚀 Quick Start

### 1. Clone or open the repository

```bash
git clone <your_repo_url>
cd BIS5151E_Research-Assistant
```

### 2. Set up the virtual environment

```
python -m venv .venv
.venv\Scripts\activate          # Windows
# or
source .venv/bin/activate       # macOS/Linux
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 3. Configure and run the project

```
python src/app/main.py
```

---

## 🧠 License
This project is for educational and non-commercial use within the M.Sc. Information Systems program at Hochschule Pforzheim.  
All AI models and datasets used must comply with open-source or institutional usage rights.
