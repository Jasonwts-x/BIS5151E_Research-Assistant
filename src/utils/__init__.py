"""
Utility Functions Module.

Configuration management and shared helper functions.

This module provides:
    - Configuration loading and validation (config.py)
    - Centralized logging setup (logging.py)
    - Environment validation (validation.py)

All utility functions are designed to be service-agnostic and
reusable across the API gateway, CrewAI service, and RAG pipeline.
"""
from __future__ import annotations