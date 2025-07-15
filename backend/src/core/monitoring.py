"""
Monitoring and observability setup.
Includes Prometheus metrics, OpenTelemetry tracing, and Sentry error tracking.
"""

import time
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Callable, Dict, Optional

import sentry_sdk
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "prism_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "prism_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)

ACTIVE_REQUESTS = Gauge(
    "prism_http_requests_active",
    "Active HTTP requests"
)

LLM_REQUEST_COUNT = Counter(
    "prism_llm_requests_total",
    "Total LLM API requests",
    ["provider", "model", "status"]
)

LLM_REQUEST_DURATION = Histogram(
    "prism_llm_request_duration_seconds",
    "LLM API request duration",
    ["provider", "model"]
)

LLM_TOKEN_COUNT = Counter(
    "prism_llm_tokens_total",
    "Total LLM tokens used",
    ["provider", "model", "type"]  # type: prompt/completion
)

AGENT_EXECUTION_COUNT = Counter(
    "prism_agent_executions_total",
    "Total agent executions",
    ["agent_type", "status"]
)

AGENT_EXECUTION_DURATION = Histogram(
    "prism_agent_execution_duration_seconds",
    "Agent execution duration",
    ["agent_type"]
)

CACHE_OPERATIONS = Counter(
    "prism_cache_operations_total",
    "Total cache operations",
    ["operation", "status"]  # operation: get/set/delete, status: hit/miss/error
)

DATABASE_OPERATIONS = Counter(
    "prism_database_operations_total",
    "Total database operations",
    ["operation", "table", "status"]
)

BACKGROUND_TASK_COUNT = Counter(
    "prism_background_tasks_total",
    "Total background tasks",
    ["task_name", "status"]
)

ERROR_COUNT = Counter(
    "prism_errors_total",
    "Total errors",
    ["error_type", "component"]
)

APP_INFO = Info(
    "prism_app",
    "Application information"
)


def setup_monitoring(app: Optional[Any] = None) -> None:
    """
    Setup monitoring and observability.
    
    Args:
        app: FastAPI application instance
    """
    # Setup application info
    APP_INFO.info({
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    })
    
    # Setup Sentry
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            before_send=_before_send_sentry,
        )
        logger.info("sentry_initialized", environment=settings.SENTRY_ENVIRONMENT)
    
    # Setup OpenTelemetry
    if settings.OTEL_ENABLED:
        # Create resource
        resource = Resource.create({
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.APP_ENV,
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            insecure=True,  # Use secure=False for local development
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Instrument libraries
        if app:
            FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        RedisInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument()
        
        logger.info("opentelemetry_initialized", endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)


def _before_send_sentry(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter Sentry events before sending.
    
    Args:
        event: Sentry event
        hint: Event hint
        
    Returns:
        Modified event or None to drop
    """
    # Don't send events in development unless explicitly enabled
    if settings.is_development and not settings.APP_DEBUG:
        return None
    
    # Filter out sensitive data
    if "request" in event:
        headers = event["request"].get("headers", {})
        # Remove authorization headers
        headers.pop("authorization", None)
        headers.pop("x-api-key", None)
    
    return event


def track_request(method: str, endpoint: str, status: int, duration: float) -> None:
    """Track HTTP request metrics."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)


def track_llm_request(
    provider: str,
    model: str,
    status: str,
    duration: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> None:
    """Track LLM request metrics."""
    LLM_REQUEST_COUNT.labels(provider=provider, model=model, status=status).inc()
    LLM_REQUEST_DURATION.labels(provider=provider, model=model).observe(duration)
    
    if prompt_tokens > 0:
        LLM_TOKEN_COUNT.labels(provider=provider, model=model, type="prompt").inc(prompt_tokens)
    if completion_tokens > 0:
        LLM_TOKEN_COUNT.labels(provider=provider, model=model, type="completion").inc(completion_tokens)


def track_agent_execution(agent_type: str, status: str, duration: float) -> None:
    """Track agent execution metrics."""
    AGENT_EXECUTION_COUNT.labels(agent_type=agent_type, status=status).inc()
    AGENT_EXECUTION_DURATION.labels(agent_type=agent_type).observe(duration)


def track_cache_operation(operation: str, status: str) -> None:
    """Track cache operation metrics."""
    CACHE_OPERATIONS.labels(operation=operation, status=status).inc()


def track_database_operation(operation: str, table: str, status: str) -> None:
    """Track database operation metrics."""
    DATABASE_OPERATIONS.labels(operation=operation, table=table, status=status).inc()


def track_background_task(task_name: str, status: str) -> None:
    """Track background task metrics."""
    BACKGROUND_TASK_COUNT.labels(task_name=task_name, status=status).inc()


def track_error(error_type: str, component: str) -> None:
    """Track error metrics."""
    ERROR_COUNT.labels(error_type=error_type, component=component).inc()


@asynccontextmanager
async def track_operation(operation_name: str):
    """
    Context manager to track operation duration.
    
    Args:
        operation_name: Name of the operation
        
    Yields:
        Operation tracker
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.debug(
            "operation_completed",
            operation=operation_name,
            duration=duration
        )


def monitor_async(
    operation_name: str,
    track_errors: bool = True,
) -> Callable:
    """
    Decorator to monitor async function execution.
    
    Args:
        operation_name: Name of the operation
        track_errors: Whether to track errors
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(
                    "async_operation_completed",
                    operation=operation_name,
                    duration=duration
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "async_operation_failed",
                    operation=operation_name,
                    duration=duration,
                    error=str(e)
                )
                if track_errors:
                    track_error(type(e).__name__, operation_name)
                raise
        
        return wrapper
    return decorator


def get_metrics() -> bytes:
    """
    Get Prometheus metrics.
    
    Returns:
        Metrics in Prometheus format
    """
    return generate_latest()