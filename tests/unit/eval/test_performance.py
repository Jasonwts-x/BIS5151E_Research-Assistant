"""Tests for performance tracking."""
from __future__ import annotations

import time

from src.eval.performance import PerformanceTracker


class TestPerformanceTracker:
    """Tests for PerformanceTracker."""
    
    def test_basic_tracking(self):
        """Test basic performance tracking."""
        tracker = PerformanceTracker()
        tracker.start()
        
        with tracker.track("operation1"):
            time.sleep(0.1)
        
        with tracker.track("operation2"):
            time.sleep(0.05)
        
        tracker.stop()
        
        metrics = tracker.get_metrics()
        
        assert "operation1" in metrics
        assert "operation2" in metrics
        assert "total_time" in metrics
        assert metrics["operation1"] >= 0.1
        assert metrics["operation2"] >= 0.05
    
    def test_nested_tracking(self):
        """Test nested performance tracking."""
        tracker = PerformanceTracker()
        tracker.start()
        
        with tracker.track("outer"):
            with tracker.track("inner"):
                time.sleep(0.05)
        
        tracker.stop()
        
        metrics = tracker.get_metrics()
        assert "outer" in metrics
        assert "inner" in metrics