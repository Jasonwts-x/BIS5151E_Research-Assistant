FROM mcr.microsoft.com/devcontainers/python:3.11

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl wget git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/BIS5151E_Research-Assistant

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements.txt

USER vscode