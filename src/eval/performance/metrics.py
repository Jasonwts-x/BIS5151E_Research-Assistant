"""
Performance Metrics Calculator
Calculate performance statistics and aggregations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PerformanceMetricsCalculator:
    """Calculate and aggregate performance metrics."""

    def __init__(self):
        """Initialize calculator."""
        self.records: List[Dict[str, Any]] = []

    def add_record(self, metrics: Dict[str, float], metadata: Optional[Dict[str, Any]] = None):
        """
        Add a performance record.
        
        Args:
            metrics: Timing metrics
            metadata: Optional metadata (query, model, etc.)
        """
        record = {
            "metrics": metrics,
            "metadata": metadata or {},
        }
        self.records.append(record)
        logger.debug("Added performance record: %s", record)

    def calculate_statistics(self) -> Dict[str, Any]:
        """
        Calculate aggregate statistics across all records.
        
        Returns:
            Statistics dictionary with averages, min, max, etc.
        """
        if not self.records:
            return {
                "total_records": 0,
                "averages": {},
                "min_values": {},
                "max_values": {},
            }

        # Extract all metric names
        all_metric_names = set()
        for record in self.records:
            all_metric_names.update(record["metrics"].keys())

        # Calculate statistics for each metric
        stats = {
            "total_records": len(self.records),
            "averages": {},
            "min_values": {},
            "max_values": {},
            "totals": {},
        }

        for metric_name in all_metric_names:
            values = [
                record["metrics"][metric_name]
                for record in self.records
                if metric_name in record["metrics"]
            ]

            if values:
                stats["averages"][metric_name] = sum(values) / len(values)
                stats["min_values"][metric_name] = min(values)
                stats["max_values"][metric_name] = max(values)
                stats["totals"][metric_name] = sum(values)

        return stats

    def compare_models(self, model_key: str = "model") -> Dict[str, Any]:
        """
        Compare performance across different models.
        
        Args:
            model_key: Metadata key for model name
            
        Returns:
            Comparison statistics
        """
        model_records: Dict[str, List[Dict[str, float]]] = {}

        for record in self.records:
            model = record["metadata"].get(model_key, "unknown")
            if model not in model_records:
                model_records[model] = []
            model_records[model].append(record["metrics"])

        comparison = {}
        for model, records in model_records.items():
            if not records:
                continue

            # Calculate average total_time for this model
            total_times = [r.get("total_time", 0) for r in records]
            comparison[model] = {
                "count": len(records),
                "avg_total_time": sum(total_times) / len(total_times) if total_times else 0,
                "min_total_time": min(total_times) if total_times else 0,
                "max_total_time": max(total_times) if total_times else 0,
            }

        return comparison

    def compare_agents(self, agent_prefix: str = "agent_") -> Dict[str, Any]:
        """
        Compare performance across different agents.
        
        Args:
            agent_prefix: Prefix for agent metrics
            
        Returns:
            Agent comparison statistics
        """
        agent_times: Dict[str, List[float]] = {}

        for record in self.records:
            for metric_name, value in record["metrics"].items():
                if metric_name.startswith(agent_prefix):
                    agent_name = metric_name[len(agent_prefix):]
                    if agent_name not in agent_times:
                        agent_times[agent_name] = []
                    agent_times[agent_name].append(value)

        comparison = {}
        for agent, times in agent_times.items():
            if times:
                comparison[agent] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "total_time": sum(times),
                }

        return comparison

    def get_slowest_components(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Get slowest components across all records.
        
        Args:
            top_n: Number of slowest components to return
            
        Returns:
            List of slowest components with statistics
        """
        component_times: Dict[str, List[float]] = {}

        for record in self.records:
            for metric_name, value in record["metrics"].items():
                if metric_name == "total_time":
                    continue
                if metric_name not in component_times:
                    component_times[metric_name] = []
                component_times[metric_name].append(value)

        slowest = []
        for component, times in component_times.items():
            if times:
                slowest.append({
                    "component": component,
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "count": len(times),
                })

        # Sort by average time descending
        slowest.sort(key=lambda x: x["avg_time"], reverse=True)
        return slowest[:top_n]

    def clear(self):
        """Clear all records."""
        self.records.clear()
        logger.debug("Performance records cleared")