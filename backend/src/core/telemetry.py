"""
Simplified telemetry module with basic metrics.
"""

from functools import wraps
import time
from typing import Any, Callable

from prometheus_client import Counter, Histogram, CollectorRegistry, REGISTRY

# Create a new registry to avoid conflicts
metrics_registry = CollectorRegistry()

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=metrics_registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    registry=metrics_registry
)

# Simple metrics class
class Metrics:
    def __init__(self):
        self.counter = lambda name, desc, labels: Counter(name, desc, labels, registry=metrics_registry)
        self.histogram = lambda name, desc, labels: Histogram(name, desc, labels, registry=metrics_registry)

# Global metrics instance
metrics = Metrics()

# Decorator for async tracing
def trace_async(name: str):
    """Simple async trace decorator."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                # Log trace info (simplified)
                print(f"Trace: {name} took {duration:.3f}s")
        return wrapper
    return decorator

# Initialize function (simplified)
def init_telemetry():
    """Initialize telemetry (simplified version)."""
    pass