"""
Agent Role Definitions Module.

Individual agent roles for the research assistant crew.
Each role specializes in a specific task: writing, reviewing, fact-checking, or translating.
"""
from __future__ import annotations

from .factchecker import create_factchecker_agent
from .reviewer import create_reviewer_agent
from .translator import create_translator_agent
from .writer import create_writer_agent

__all__ = [
    "create_writer_agent",
    "create_reviewer_agent",
    "create_factchecker_agent",
    "create_translator_agent",
]