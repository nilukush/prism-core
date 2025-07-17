"""
Main FastAPI application entry point.
Configures the application, middleware, and routes.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from backend.src.core.config import settings
from backend.src.core.database import init_db, close_db
from backend.src.core.cache_unified import cache
from backend.src.core.logging import setup_logging, get_logger
from backend.src.core.monitoring import setup_monitoring, ACTIVE_REQUESTS, track_request
from backend.src.api import api_router
from backend.src.middleware.rate_limiting import RateLimitMiddleware, rate_limiter
from backend.src.middleware.ddos_protection import DDoSProtectionMiddleware
from backend.src.middleware.request_id import RequestIDMiddleware
from backend.src.middleware.security import SecurityHeadersMiddleware
from backend.src.services.vector_store import vector_store

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("application_starting", environment=settings.APP_ENV)
    
    # Setup logging
    setup_logging()
    
    # Setup monitoring
    setup_monitoring(app)
    
    # Initialize database
    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.warning("database_initialization_failed", error=str(e))
        logger.info("running_without_database")
    
    # Connect to cache
    try:
        await cache.connect()
        logger.info("cache_initialized")
    except Exception as e:
        logger.warning("cache_initialization_failed", error=str(e))
        logger.info("running_without_cache")
    
    # Initialize vector store
    try:
        await vector_store.initialize()
        logger.info("vector_store_initialized")
    except Exception as e:
        logger.warning("vector_store_initialization_failed", error=str(e))
        logger.info("running_without_vector_store")
    
    # Initialize rate limiter
    try:
        await rate_limiter.initialize()
        logger.info("rate_limiter_initialized")
    except Exception as e:
        logger.warning("rate_limiter_initialization_failed", error=str(e))
    
    # Initialize enterprise authentication
    if settings.ENVIRONMENT in ["production", "staging"] or os.getenv("USE_PERSISTENT_SESSIONS", "false").lower() == "true":
        try:
            from backend.src.services.auth_enterprise import enterprise_auth_service
            await enterprise_auth_service.initialize()
            logger.info("enterprise_auth_initialized", persistent_sessions=True)
        except Exception as e:
            logger.warning("enterprise_auth_initialization_failed", error=str(e))
            logger.info("falling_back_to_in_memory_sessions")
    
    logger.info("application_started")
    
    yield
    
    # Shutdown
    logger.info("application_stopping")
    
    # Prepare enterprise auth for shutdown
    if settings.ENVIRONMENT in ["production", "staging"] or os.getenv("USE_PERSISTENT_SESSIONS", "false").lower() == "true":
        try:
            from backend.src.services.auth_enterprise import enterprise_auth_service
            if enterprise_auth_service.session_manager:
                await enterprise_auth_service.prepare_shutdown()
                logger.info("enterprise_auth_shutdown_prepared")
        except Exception as e:
            logger.error("enterprise_auth_shutdown_error", error=str(e))
    
    # Close connections
    try:
        await cache.disconnect()
    except Exception:
        pass
    
    try:
        await close_db()
    except Exception:
        pass
        
    try:
        await vector_store.close()
    except Exception:
        pass
    
    logger.info("application_stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Open source AI-powered product management platform",
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json" if not settings.is_production else None,
    docs_url=f"{settings.API_PREFIX}/docs" if not settings.is_production else None,
    redoc_url=f"{settings.API_PREFIX}/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# Add middleware in correct order (last added = first executed)
# 1. Security headers and OWASP protection
app.add_middleware(SecurityHeadersMiddleware)

# 2. DDoS protection (before rate limiting)
if settings.DDOS_PROTECTION_ENABLED:
    app.add_middleware(DDoSProtectionMiddleware)

# 3. Rate limiting
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

# 4. CORS (after security checks)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 5. Trusted host checking (production only)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.prism-ai.dev", "prism-ai.dev", "localhost"],
    )

# 6. Request ID (should be early in chain)
app.add_middleware(RequestIDMiddleware)

# Mount Prometheus metrics endpoint
if settings.PROMETHEUS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track HTTP request metrics."""
    ACTIVE_REQUESTS.inc()
    
    try:
        response = await call_next(request)
        return response
    finally:
        ACTIVE_REQUESTS.dec()


# Include API routes
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    checks = {
        "database": False,
        "cache": False,
        "vector_store": False,
    }
    
    # Check database
    try:
        from backend.src.core.database import engine
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        checks["database"] = True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
    
    # Check cache
    try:
        await cache.set("health_check", "ok", ttl=10)
        checks["cache"] = await cache.get("health_check") == "ok"
    except Exception as e:
        logger.error("cache_health_check_failed", error=str(e))
    
    # Check vector store
    try:
        checks["vector_store"] = await vector_store.health_check()
    except Exception as e:
        logger.error("vector_store_health_check_failed", error=str(e))
    
    all_healthy = all(checks.values())
    
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={
            "ready": all_healthy,
            "checks": checks,
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": "The requested resource was not found",
            "path": str(request.url.path),
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler."""
    logger.error(
        "internal_server_error",
        path=str(request.url.path),
        method=request.method,
        exc_info=exc,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_config=None,  # Use our custom logging
    )