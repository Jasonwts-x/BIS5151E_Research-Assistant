"""
Agent Role Definitions
Individual agent roles for the research assistant crew.
Each role specializes in a specific task: writing, reviewing, or fact-checking.
"""
from __future__ import annotations

from .factchecker import create_factchecker_agent
from .reviewer import create_reviewer_agent
from .writer import create_writer_agent

__all__ = [
    "create_writer_agent",
    "create_reviewer_agent",
    "create_factchecker_agent",

]
