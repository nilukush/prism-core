"""
Enhanced FastAPI application with enterprise features.
Includes OpenTelemetry, structured logging, and comprehensive monitoring.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import make_asgi_app
import structlog

from backend.src.core.config import settings
from backend.src.core.database import init_db, close_db
from backend.src.core.cache import cache
from backend.src.core.logging import setup_logging, get_logger
from backend.src.core.monitoring import setup_monitoring
from backend.src.core.telemetry import setup_telemetry, TelemetryMiddleware, tracer
from backend.src.api import api_router
from backend.src.middleware.rate_limit import RateLimitMiddleware
from backend.src.middleware.request_id import RequestIDMiddleware
from backend.src.middleware.security import SecurityHeadersMiddleware
from backend.src.services.vector_store import vector_store

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to all requests for distributed tracing."""
    
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        # Bind to structlog context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4())),
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else "unknown"
        )
        
        # Add span attributes if tracing is enabled
        if tracer:
            span = tracer.get_current_span()
            if span and span.is_recording():
                span.set_attribute("correlation.id", correlation_id)
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        
        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Enhanced compression middleware with content type checking."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only compress certain content types
        content_type = response.headers.get("content-type", "")
        compressible_types = [
            "application/json",
            "text/html",
            "text/plain",
            "text/css",
            "text/javascript",
            "application/javascript"
        ]
        
        should_compress = any(ct in content_type for ct in compressible_types)
        
        if should_compress and "gzip" in request.headers.get("accept-encoding", ""):
            # Response size threshold for compression (1KB)
            if int(response.headers.get("content-length", 0)) > 1024:
                response.headers["vary"] = "Accept-Encoding"
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Enhanced application lifespan manager.
    Handles startup and shutdown events with proper error handling.
    """
    # Startup
    logger.info(
        "application_starting",
        environment=settings.APP_ENV,
        version=settings.APP_VERSION,
        debug=settings.APP_DEBUG
    )
    
    # Setup logging first
    setup_logging()
    
    # Setup telemetry
    tracer, meter = setup_telemetry(app)
    logger.info("telemetry_initialized", otel_enabled=settings.OTEL_ENABLED)
    
    # Setup monitoring
    setup_monitoring(app)
    logger.info("monitoring_initialized", prometheus_enabled=settings.PROMETHEUS_ENABLED)
    
    # Initialize database
    try:
        await init_db()
        logger.info("database_initialized", pool_size=settings.DATABASE_POOL_SIZE)
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e), exc_info=True)
        if settings.is_production:
            raise  # Fail fast in production
        logger.warning("running_without_database")
    
    # Connect to cache
    try:
        await cache.connect()
        logger.info("cache_initialized", redis_url=str(settings.REDIS_URL))
    except Exception as e:
        logger.error("cache_initialization_failed", error=str(e), exc_info=True)
        if settings.is_production:
            raise  # Fail fast in production
        logger.warning("running_without_cache")
    
    # Initialize vector store
    try:
        await vector_store.initialize()
        logger.info("vector_store_initialized", url=settings.QDRANT_URL)
    except Exception as e:
        logger.warning("vector_store_initialization_failed", error=str(e))
        logger.info("running_without_vector_store")
    
    # Log startup metrics
    if meter:
        startup_time = meter.create_counter(
            name="prism.startup.count",
            description="Application startup count"
        )
        startup_time.add(1, {"environment": settings.APP_ENV})
    
    logger.info(
        "application_started",
        startup_time_ms=f"{(time.time() - app.state.startup_time) * 1000:.2f}"
    )
    
    yield
    
    # Shutdown
    logger.info("application_stopping")
    
    # Graceful shutdown with timeout
    shutdown_timeout = 30  # seconds
    shutdown_start = time.time()
    
    # Close connections
    try:
        await cache.disconnect()
        logger.info("cache_disconnected")
    except Exception as e:
        logger.error("cache_disconnect_error", error=str(e))
    
    try:
        await close_db()
        logger.info("database_disconnected")
    except Exception as e:
        logger.error("database_disconnect_error", error=str(e))
    
    try:
        await vector_store.close()
        logger.info("vector_store_disconnected")
    except Exception as e:
        logger.error("vector_store_disconnect_error", error=str(e))
    
    shutdown_duration = time.time() - shutdown_start
    logger.info(
        "application_stopped",
        shutdown_duration_seconds=shutdown_duration
    )


# Create FastAPI application with enhanced configuration
app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade AI-powered product management platform",
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json" if not settings.is_production else None,
    docs_url=f"{settings.API_PREFIX}/docs" if not settings.is_production else None,
    redoc_url=f"{settings.API_PREFIX}/redoc" if not settings.is_production else None,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "Authentication endpoints"},
        {"name": "users", "description": "User management"},
        {"name": "projects", "description": "Project management"},
        {"name": "stories", "description": "User story management"},
        {"name": "ai", "description": "AI-powered features"},
        {"name": "health", "description": "Health check endpoints"},
    ]
)

# Store startup time
app.state.startup_time = time.time()

# Add middleware in correct order (outermost to innermost)

# 1. Correlation ID (outermost - needs to be available for all other middleware)
app.add_middleware(CorrelationIdMiddleware)

# 2. Request ID
app.add_middleware(RequestIDMiddleware)

# 3. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 4. Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 5. Rate limiting
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

# 6. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=["X-Correlation-ID", "X-Request-ID", "X-Response-Time"]
)

# 7. Trusted hosts (production only)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.prism-ai.dev", "prism-ai.dev", "localhost"]
    )

# 8. Telemetry (closest to the application)
if settings.OTEL_ENABLED:
    app.add_middleware(TelemetryMiddleware)

# Mount Prometheus metrics endpoint
if settings.PROMETHEUS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


# Global exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Enhanced 404 handler with correlation ID."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.warning(
        "resource_not_found",
        path=str(request.url.path),
        method=request.method,
        correlation_id=correlation_id
    )
    
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": "The requested resource was not found",
            "path": str(request.url.path),
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Enhanced 500 handler with detailed logging."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.error(
        "internal_server_error",
        path=str(request.url.path),
        method=request.method,
        correlation_id=correlation_id,
        exc_info=exc
    )
    
    # In production, don't expose error details
    if settings.is_production:
        message = "An unexpected error occurred"
    else:
        message = str(exc) if exc else "An unexpected error occurred"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": message,
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.error(
        "unhandled_exception",
        path=str(request.url.path),
        method=request.method,
        correlation_id=correlation_id,
        exception_type=type(exc).__name__,
        exc_info=exc
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id
        }
    )


# Include API routes
app.include_router(api_router, prefix=settings.API_PREFIX)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": f"{settings.API_PREFIX}/docs" if not settings.is_production else None,
        "health": "/health",
        "metrics": "/metrics" if settings.PROMETHEUS_ENABLED else None
    }


# Health check endpoints (outside API prefix for infrastructure)
@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": time.time()
    }


@app.get("/health/live", tags=["health"])
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive", "timestamp": time.time()}


@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    Checks critical dependencies.
    """
    checks = {
        "database": False,
        "cache": False,
        "vector_store": False
    }
    errors = []
    
    # Check database
    try:
        from backend.src.core.database import get_db
        async for db in get_db():
            await db.execute("SELECT 1")
            checks["database"] = True
            break
    except Exception as e:
        errors.append(f"database: {str(e)}")
    
    # Check cache
    try:
        await cache.ping()
        checks["cache"] = True
    except Exception as e:
        errors.append(f"cache: {str(e)}")
    
    # Check vector store (optional)
    try:
        if await vector_store.health_check():
            checks["vector_store"] = True
    except Exception as e:
        # Vector store is optional
        checks["vector_store"] = None
    
    # Determine if service is ready
    required_checks = ["database", "cache"]
    is_ready = all(checks.get(check, False) for check in required_checks)
    
    response_data = {
        "ready": is_ready,
        "checks": checks,
        "timestamp": time.time()
    }
    
    if errors:
        response_data["errors"] = errors
    
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content=response_data
    )


if __name__ == "__main__":
    import uvicorn
    
    # Configure uvicorn with production settings
    uvicorn.run(
        "backend.src.main_enhanced:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_config=None,  # Use our custom logging
        access_log=False,  # We handle access logs in middleware
        workers=1 if settings.is_development else 4,
        loop="uvloop",  # High-performance event loop
        limit_concurrency=1000,
        limit_max_requests=10000 if settings.is_production else None,  # Restart workers periodically
    )