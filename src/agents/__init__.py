"""
CrewAI Agents Module
Multi-agent research assistant powered by CrewAI.
Provides crew runner for orchestrating Writer, Reviewer, and FactChecker agents.
"""
from __future__ import annotations

from .runner import CrewRunner, get_crew_runner



__all__ = ["CrewRunner", "get_crew_runner"]