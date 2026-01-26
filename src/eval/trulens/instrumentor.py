"""
TruLens Instrumentation
Instrument pipelines and workflows for tracking.
"""
from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def instrument_pipeline(func: Callable) -> Callable:
    """
    Decorator to instrument RAG pipeline functions.

    Usage:
        @instrument_pipeline
        def rag_query(query: str, top_k: int = 5):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # TODO: Full TruLens instrumentation
        # For now, just log
        logger.info("RAG Pipeline called: %s", func.__name__)
        result = func(*args, **kwargs)
        logger.info("RAG Pipeline completed")
        return result
    
    return wrapper


def instrument_crew(func: Callable) -> Callable:
    """
    Decorator to instrument CrewAI workflow functions.

    Usage:
        @instrument_crew
        def run_crew(topic: str):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # TODO: Full TruLens instrumentation
        # For now, just log
        logger.info("Crew workflow called: %s", func.__name__)
        result = func(*args, **kwargs)
        logger.info("Crew workflow completed")
        return result
    
    return wrapper


class TruLensInstrumentor:
    """Helper class for instrumenting components."""

    def __init__(self, enabled: bool = True):
        """
        Initialize instrumentor.

        Args:
            enabled: Whether instrumentation is enabled
        """
        self.enabled = enabled
        logger.info("TruLensInstrumentor initialized (enabled=%s)", enabled)

    def instrument_function(
        self,
        func: Callable,
        metadata: Optional[dict] = None,
    ) -> Callable:
        """
        Instrument a function for tracking.

        Args:
            func: Function to instrument
            metadata: Optional metadata

        Returns:
            Instrumented function
        """
        if not self.enabled:
            return func

        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug("Instrumented function called: %s", func.__name__)
            result = func(*args, **kwargs)
            logger.debug("Instrumented function completed: %s", func.__name__)
            return result

        return wrapper