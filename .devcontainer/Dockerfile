# ==============================================================================
# Multi-stage Dockerfile for Research Assistant Services
# ==============================================================================
# Targets:
#   - base: Common Python environment with all dependencies
#   - dev:  Development container (DevContainer)
#   - api:  Main API gateway service
#   - crewai: CrewAI agent service
# ==============================================================================

# ------------------------------------------------------------------------------
# BASE STAGE: Common Python environment
# ------------------------------------------------------------------------------

FROM mcr.microsoft.com/devcontainers/python:3.11 AS base

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl wget git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/BIS5151E_Research-Assistant

# Copy and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements.txt

# ------------------------------------------------------------------------------
# DEV STAGE: Development container (for DevContainer)
# ------------------------------------------------------------------------------

FROM base AS dev

USER vscode

# Development-specific tools can be added here if needed

# ------------------------------------------------------------------------------
# API STAGE: Main API gateway service
# ------------------------------------------------------------------------------

FROM base AS api

USER vscode

# API service runs: uvicorn src.api.server:app
# Configured in docker-compose.yml

# ------------------------------------------------------------------------------
# CREW STAGE: CrewAI agent service
# ------------------------------------------------------------------------------

FROM base AS crewai

USER vscode

# CrewAI service runs: uvicorn src.agents.api.server:app
# Configured in docker-compose.yml