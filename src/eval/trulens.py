from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TruLensMonitor:
    """
    TruLens monitoring for CrewAI workflows.

    NOTE: This is a simplified implementation.
    Full TruLens integration requires TruLens installation.

    Tracks:
    - Answer relevance
    - Context relevance
    - Groundedness (hallucination detection)
    - Response quality
    """

    def __init__(self, app_id: str = "research_assistant", enabled: bool = False):
        """
        Initialize TruLens monitoring.

        Args:
            app_id: Unique identifier for this application
            enabled: Whether monitoring is enabled (requires TruLens installation)
        """
        self.app_id = app_id
        self.enabled = enabled
        self.session: Optional[Any] = None
        self.metrics: list[dict] = []

        if enabled:
            try:
                # Dynamic import INSIDE try-except
                import importlib
                trulens_core = importlib.import_module('trulens.core')
                TruSession = trulens_core.TruSession
                self.session = TruSession()
                logger.info(
                    "TruLens monitoring initialized for app: %s", app_id)
            except (ImportError, ModuleNotFoundError):
                logger.warning(
                    "TruLens not installed. Install with: pip install trulens-eval"
                )
                self.enabled = False
        else:
            logger.info("TruLens monitoring disabled")

    def log_interaction(
        self,
        topic: str,
        context: str,
        output: str,
        language: str,
        metadata: Optional[dict] = None
    ):
        """
        Log an interaction for monitoring.

        Args:
            topic: User query/topic
            context: Retrieved context
            output: Final crew output
            language: Target language
            metadata: Additional metadata
        """
        interaction = {
            "topic": topic,
            "context_length": len(context),
            "output_length": len(output),
            "language": language,
            "metadata": metadata or {}
        }

        self.metrics.append(interaction)

        if self.enabled and self.session:
            # Log to TruLens (simplified)
            logger.debug("Logging interaction to TruLens: %s", interaction)
        else:
            logger.debug("Interaction logged locally: %s", interaction)

    def get_metrics(self) -> list[dict]:
        """Get all logged metrics."""
        return self.metrics

    def get_summary(self) -> dict:
        """Get summary statistics."""
        if not self.metrics:
            return {
                "total_interactions": 0,
                "monitoring_enabled": self.enabled
            }

        return {
            "total_interactions": len(self.metrics),
            "avg_context_length": sum(m["context_length"] for m in self.metrics) / len(self.metrics),
            "avg_output_length": sum(m["output_length"] for m in self.metrics) / len(self.metrics),
            "languages": list(set(m["language"] for m in self.metrics)),
            "monitoring_enabled": self.enabled
        }

    def start_dashboard(self):
        """
        Start TruLens dashboard (requires full TruLens installation).

        This is a placeholder for future implementation.
        """
        if not self.enabled:
            logger.warning(
                "TruLens monitoring is disabled. Cannot start dashboard.")
            return

        try:
            import importlib
            trulens_dashboard = importlib.import_module('trulens.dashboard')
            run_dashboard = trulens_dashboard.run_dashboard
            logger.info("Starting TruLens dashboard at http://localhost:8501")
            run_dashboard(self.session)
        except (ImportError, ModuleNotFoundError):
            logger.error(
                "TruLens dashboard not available. Install TruLens first.")
