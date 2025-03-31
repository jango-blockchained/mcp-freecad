import logging
import time
import asyncio
import os
import platform
import sys
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from collections import deque
from functools import wraps

logger = logging.getLogger(__name__)

class PerformanceMetric:
    """
    Performance metric for tracking response times and other metrics.
    """
    
    def __init__(self, name: str, max_samples: int = 100):
        """
        Initialize a performance metric.
        
        Args:
            name: Name of the metric
            max_samples: Maximum number of samples to keep
        """
        self.name = name
        self.max_samples = max_samples
        self.samples = deque(maxlen=max_samples)
        self.total_calls = 0
        self.total_errors = 0
        self.last_error = None
        self.last_error_time = 0
        
    def record_sample(self, duration: float, success: bool = True, error: Optional[Exception] = None) -> None:
        """
        Record a new sample.
        
        Args:
            duration: Duration of the operation in seconds
            success: Whether the operation was successful
            error: Exception if operation failed
        """
        self.samples.append({
            "timestamp": time.time(),
            "duration": duration,
            "success": success
        })
        self.total_calls += 1
        
        if not success:
            self.total_errors += 1
            self.last_error = str(error) if error else "Unknown error"
            self.last_error_time = time.time()
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics for this metric.
        
        Returns:
            Dictionary with metric statistics
        """
        if not self.samples:
            return {
                "name": self.name,
                "total_calls": self.total_calls,
                "total_errors": self.total_errors,
                "error_rate": 0,
                "avg_duration": 0,
                "min_duration": 0,
                "max_duration": 0,
                "last_error": self.last_error,
                "last_error_time": self.last_error_time
            }
            
        durations = [s["duration"] for s in self.samples]
        success_rate = sum(1 for s in self.samples if s["success"]) / len(self.samples)
        
        return {
            "name": self.name,
            "total_calls": self.total_calls,
            "total_errors": self.total_errors,
            "error_rate": 1.0 - success_rate,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "last_error": self.last_error,
            "last_error_time": self.last_error_time,
            "sample_count": len(self.samples),
            "recent_calls": [
                {
                    "timestamp": s["timestamp"], 
                    "duration": s["duration"], 
                    "success": s["success"]
                } 
                for s in list(self.samples)[-5:]
            ]
        }

class PerformanceMonitor:
    """
    Performance monitoring for the MCP server.
    
    This class tracks performance metrics like response times,
    error rates, and resource usage.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        logger.info("Initialized performance monitor")
        
    def track(self, name: str = None, max_samples: int = 100):
        """
        Decorator to track performance of a function.
        
        Args:
            name: Optional custom name for the metric
            max_samples: Maximum number of samples to keep
            
        Returns:
            Decorator function
        """
        def decorator(func):
            metric_name = name or f"{func.__module__}.{func.__name__}"
            
            if metric_name not in self.metrics:
                self.metrics[metric_name] = PerformanceMetric(metric_name, max_samples)
                
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = e
                    self.error_count += 1
                    raise
                finally:
                    duration = time.time() - start_time
                    self.request_count += 1
                    self.metrics[metric_name].record_sample(duration, success, error)
                    
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = e
                    self.error_count += 1
                    raise
                finally:
                    duration = time.time() - start_time
                    self.request_count += 1
                    self.metrics[metric_name].record_sample(duration, success, error)
            
            # Choose the appropriate wrapper based on whether the function is async
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
                
        return decorator
        
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system resource statistics.
        
        Returns:
            Dictionary with system statistics
        """
        try:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            
            return {
                "cpu_percent": process.cpu_percent(),
                "memory_usage": {
                    "rss": mem_info.rss / (1024 * 1024),  # MB
                    "vms": mem_info.vms / (1024 * 1024),  # MB
                },
                "thread_count": threading.active_count(),
                "python_version": sys.version,
                "platform": platform.platform(),
                "system_memory": {
                    "total": psutil.virtual_memory().total / (1024 * 1024),  # MB
                    "available": psutil.virtual_memory().available / (1024 * 1024),  # MB
                    "percent": psutil.virtual_memory().percent
                }
            }
        except Exception as e:
            logger.warning(f"Error getting system stats: {e}")
            return {
                "error": str(e)
            }
            
    def get_server_stats(self) -> Dict[str, Any]:
        """
        Get server statistics.
        
        Returns:
            Dictionary with server statistics
        """
        uptime = time.time() - self.start_time
        
        return {
            "uptime": uptime,
            "uptime_formatted": _format_duration(uptime),
            "start_time": self.start_time,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(1, self.request_count),
            "metric_count": len(self.metrics)
        }
        
    def get_metrics(self, include_details: bool = False) -> List[Dict[str, Any]]:
        """
        Get all tracked metrics.
        
        Args:
            include_details: Whether to include detailed samples
            
        Returns:
            List of metric statistics
        """
        metrics = []
        
        for name, metric in self.metrics.items():
            stats = metric.get_stats()
            
            if not include_details:
                # Remove detailed samples to reduce response size
                if "recent_calls" in stats:
                    del stats["recent_calls"]
                    
            metrics.append(stats)
            
        # Sort by average duration (slowest first)
        return sorted(metrics, key=lambda m: m.get("avg_duration", 0), reverse=True)
        
    def get_diagnostics_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive diagnostics report.
        
        Returns:
            Dictionary with comprehensive diagnostics information
        """
        return {
            "server": self.get_server_stats(),
            "system": self.get_system_stats(),
            "metrics": self.get_metrics(include_details=False),
            "timestamp": time.time()
        }
        
    def reset_metrics(self) -> None:
        """Reset all performance metrics."""
        self.metrics = {}
        self.request_count = 0
        self.error_count = 0
        logger.info("Reset all performance metrics")

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