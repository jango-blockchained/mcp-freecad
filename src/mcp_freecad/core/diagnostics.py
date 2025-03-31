import logging
import time
import asyncio
import os
import platform
import sys
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from collections import deque, defaultdict
from functools import wraps
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class MetricSample:
    """A single sample of a performance metric."""
    timestamp: float
    duration: float
    success: bool
    error: Optional[str] = None

@dataclass
class Metric:
    """A performance metric with samples."""
    name: str
    samples: List[MetricSample] = field(default_factory=list)
    total_samples: int = 0
    total_duration: float = 0.0
    success_count: int = 0
    error_count: int = 0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    avg_duration: float = 0.0

    def record_sample(self, duration: float, success: bool, error: Optional[str] = None) -> None:
        """Record a new sample for this metric."""
        self.samples.append(MetricSample(
            timestamp=time.time(),
            duration=duration,
            success=success,
            error=error
        ))
        self.total_samples += 1
        self.total_duration += duration
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        self.min_duration = min(self.min_duration, duration)
        self.max_duration = max(self.max_duration, duration)
        self.avg_duration = self.total_duration / self.total_samples

class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics: Dict[str, Metric] = {}
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.warning_counts: Dict[str, int] = defaultdict(int)
        
    def track(self, metric_name: str, duration: float, success: bool = True, error: Optional[str] = None) -> Metric:
        """Get or create a metric tracker and record a sample."""
        metric = self.metrics.get(metric_name)
        if metric is None:
            metric = Metric(name=metric_name)
            self.metrics[metric_name] = metric
        metric.record_sample(duration, success, error)
        return metric
        
    def record_error(self, error_type: str, message: str) -> None:
        """Record an error occurrence."""
        self.error_counts[error_type] += 1
        logger.error(f"{error_type}: {message}")
        
    def record_warning(self, warning_type: str, message: str) -> None:
        """Record a warning occurrence."""
        self.warning_counts[warning_type] += 1
        logger.warning(f"{warning_type}: {message}")
        
    def get_diagnostics_report(self) -> Dict[str, Any]:
        """Generate a diagnostics report."""
        return {
            "uptime": time.time() - self.start_time,
            "metrics": {
                name: {
                    "total_samples": metric.total_samples,
                    "success_count": metric.success_count,
                    "error_count": metric.error_count,
                    "min_duration": metric.min_duration,
                    "max_duration": metric.max_duration,
                    "avg_duration": metric.avg_duration
                }
                for name, metric in self.metrics.items()
            },
            "errors": dict(self.error_counts),
            "warnings": dict(self.warning_counts),
            "recent_samples": {
                name: [
                    {
                        "timestamp": sample.timestamp,
                        "duration": sample.duration,
                        "success": sample.success,
                        "error": sample.error
                    }
                    for sample in metric.samples[-10:]  # Last 10 samples
                ]
                for name, metric in self.metrics.items()
            }
        }
        
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        self.error_counts.clear()
        self.warning_counts.clear()
        self.start_time = time.time()
        
    def get_metric_summary(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a specific metric."""
        if metric_name not in self.metrics:
            return None
            
        metric = self.metrics[metric_name]
        return {
            "name": metric.name,
            "total_samples": metric.total_samples,
            "success_count": metric.success_count,
            "error_count": metric.error_count,
            "min_duration": metric.min_duration,
            "max_duration": metric.max_duration,
            "avg_duration": metric.avg_duration,
            "recent_samples": [
                {
                    "timestamp": sample.timestamp,
                    "duration": sample.duration,
                    "success": sample.success,
                    "error": sample.error
                }
                for sample in metric.samples[-5:]  # Last 5 samples
            ]
        }
        
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all errors."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_types": dict(self.error_counts),
            "total_warnings": sum(self.warning_counts.values()),
            "warning_types": dict(self.warning_counts)
        }

def _format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{int(days)}d")
    if hours > 0 or days > 0:
        parts.append(f"{int(hours)}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{int(minutes)}m")
        
    parts.append(f"{int(seconds)}s")
    
    return " ".join(parts) 