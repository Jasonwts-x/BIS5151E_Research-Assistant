# .devcontainer/Dockerfile
# ==============================================================================
# Multi-stage Dockerfile for Research Assistant Services
# ==============================================================================
# Optimized for:
# - Layer caching (heavy packages cached separately)
# - Faster rebuilds when adding small packages
# - Modern pip resolver (no legacy resolver!)
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

# CRITICAL: Install numpy<2.0 FIRST to prevent conflicts
RUN pip install --no-cache-dir "numpy>=1.23.5,<2.0.0"

# Install PyTorch CPU version (HEAVY - 800MB - cache this separately!)
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.9.1+cpu

# Install sentence-transformers (will use the numpy we already installed)
RUN pip install --no-cache-dir \
    sentence-transformers==3.3.1

# ==============================================================================
# Install remaining packages from requirements.txt
# Use MODERN pip resolver (removed --use-deprecated=legacy-resolver)
# ==============================================================================
COPY requirements.txt /tmp/requirements.txt

# Install with modern resolver and proper dependency resolution
RUN pip install --no-cache-dir \
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

# Download NLTK data (required for evaluation metrics)
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True); nltk.download('stopwords', quiet=True)"

# Switch to vscode user
USER vscode

# Set working directory
WORKDIR /workspaces/BIS5151E_Research-Assistant