"""
Performance Tracker
Decorators and context managers for tracking execution time.
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Generator, Optional

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Tracks performance metrics for workflow execution.
    
    Usage:
        tracker = PerformanceTracker()
        
        with tracker.track("rag_retrieval"):
            # ... rag code ...
        
        with tracker.track("agent_writer"):
            # ... writer agent code ...
        
        metrics = tracker.get_metrics()
    """

    def __init__(self):
        """Initialize tracker."""
        self.metrics: Dict[str, float] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self._active_timers: Dict[str, float] = {}

    def start(self):
        """Start overall timer."""
        self.start_time = time.time()
        logger.debug("Performance tracking started")

    def stop(self):
        """Stop overall timer."""
        self.end_time = time.time()
        if self.start_time:
            total_time = self.end_time - self.start_time
            self.metrics["total_time"] = total_time
            logger.info("Performance tracking stopped. Total time: %.2fs", total_time)

    @contextmanager
    def track(self, name: str) -> Generator[None, None, None]:
        """
        Context manager to track execution time of a code block.
        
        Args:
            name: Name of the operation being tracked
            
        Usage:
            with tracker.track("operation_name"):
                # ... code to track ...
        """
        start = time.time()
        self._active_timers[name] = start
        logger.debug("Started tracking: %s", name)
        
        try:
            yield
        finally:
            elapsed = time.time() - start
            self.metrics[name] = elapsed
            del self._active_timers[name]
            logger.debug("Finished tracking %s: %.2fs", name, elapsed)

    def get_metrics(self) -> Dict[str, float]:
        """
        Get all tracked metrics.
        
        Returns:
            Dictionary of metric_name -> time_in_seconds
        """
        return self.metrics.copy()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary with calculated statistics.
        
        Returns:
            Summary dictionary with totals and breakdowns
        """
        if not self.metrics:
            return {"total_time": 0.0, "components": {}}

        total = self.metrics.get("total_time", sum(self.metrics.values()))
        
        return {
            "total_time": total,
            "components": self.metrics.copy(),
            "percentages": {
                name: (time_val / total * 100) if total > 0 else 0
                for name, time_val in self.metrics.items()
                if name != "total_time"
            },
        }

    def reset(self):
        """Reset all metrics."""
        self.metrics.clear()
        self._active_timers.clear()
        self.start_time = None
        self.end_time = None
        logger.debug("Performance tracker reset")


def track_performance(name: str) -> Callable:
    """
    Decorator to track function execution time.
    
    Usage:
        @track_performance("my_function")
        def my_function():
            # ... code ...
    
    Args:
        name: Name for the tracked metric
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            logger.debug("Performance tracking started: %s", name)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start
                logger.info("Performance: %s completed in %.2fs", name, elapsed)
        
        return wrapper
    return decorator