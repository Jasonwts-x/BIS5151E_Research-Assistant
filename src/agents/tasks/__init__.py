"""
Agent Task Definitions
Task specifications for each agent role.
Defines what each agent should do and the expected output format.
"""
from __future__ import annotations

from .factchecker import create_factchecker_task
from .reviewer import create_reviewer_task
from .translator import create_translator_task
from .writer import create_writer_task

__all__ = [
    "create_writer_task",
    "create_reviewer_task",
    "create_factchecker_task",
    "create_translator_task",
]