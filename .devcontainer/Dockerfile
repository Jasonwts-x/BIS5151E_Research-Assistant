# ==============================================================================
# Multi-stage Dockerfile for Research Assistant Services
# ==============================================================================
# Optimized for:
# - Layer caching (heavy packages cached separately)
# - Faster rebuilds when adding small packages
# - Dependency resolution fixes
# ==============================================================================

# ------------------------------------------------------------------------------
# BASE STAGE: Common Python environment with all dependencies
# ------------------------------------------------------------------------------
FROM mcr.microsoft.com/devcontainers/python:3.11 AS base

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl wget git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/BIS5151E_Research-Assistant

# ==============================================================================
# OPTIMIZATION: Install heavy packages in separate layers
# This prevents re-downloading PyTorch when requirements.txt changes
# ==============================================================================
RUN python -m pip install --upgrade pip

# Install PyTorch (HEAVY - 800MB - cache this separately!)
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    # torch==2.5.1+cpu
    torch==2.9.1+cpu

# Install other heavy ML packages (cache separately)
RUN pip install --no-cache-dir \
    sentence-transformers==3.3.1

# ==============================================================================
# Install remaining packages from requirements.txt
# Use legacy resolver to avoid dependency resolution loops
# ==============================================================================
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir \
    --use-deprecated=legacy-resolver \
    --default-timeout=100 \
    --retries=5 \
    -r /tmp/requirements.txt

# ------------------------------------------------------------------------------
# DEV STAGE: Development container (for DevContainer)
# ------------------------------------------------------------------------------
FROM base AS dev
USER vscode

# ------------------------------------------------------------------------------
# API STAGE: Main API gateway service
# ------------------------------------------------------------------------------
FROM base AS api
USER vscode

# ------------------------------------------------------------------------------
# CREW STAGE: CrewAI agent service
# ------------------------------------------------------------------------------
FROM base AS crewai
USER vscode

# ------------------------------------------------------------------------------
# EVAL STAGE: Evaluation service
# ------------------------------------------------------------------------------
FROM base AS eval

# Download NLTK data (required for ROUGE metrics)
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"


# Create startup script to run both services concurrently
RUN echo '#!/bin/bash\n\
    set -e\n\
    echo "🚀 Starting Evaluation Service..."\n\
    uvicorn src.eval.api.server:app --host 0.0.0.0 --port 8502 &\n\
    FASTAPI_PID=$!\n\
    echo "✅ FastAPI started (PID $FASTAPI_PID)"\n\
    \n\
    echo "🚀 Starting Streamlit Dashboard..."\n\
    streamlit run src/eval/dashboard/app.py --server.port 8501 --server.address 0.0.0.0 &\n\
    STREAMLIT_PID=$!\n\
    echo "✅ Streamlit started (PID $STREAMLIT_PID)"\n\
    \n\
    echo "📊 Evaluation service ready on ports 8501 (dashboard) and 8502 (API)"\n\
    wait $FASTAPI_PID $STREAMLIT_PID\n\
    ' > /workspaces/BIS5151E_Research-Assistant/start_eval.sh \
    && chmod +x /workspaces/BIS5151E_Research-Assistant/start_eval.sh

# Switch to vscode user for consistency
USER vscode

# Run both services
CMD ["/workspaces/BIS5151E_Research-Assistant/start_eval.sh"]