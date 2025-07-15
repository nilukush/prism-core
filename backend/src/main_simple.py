"""
Simplified FastAPI application for PRISM.
This is a minimal version to get the application running.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from backend.src.core.config import settings
from backend.src.core.database import engine
from backend.src.models.base import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting PRISM API...")
    
    # Create database tables if needed
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.warning(f"Could not create tables: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PRISM API...")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Product Management Platform",
    version=settings.VERSION,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "prism-backend",
        "version": settings.VERSION,
    }


# API info endpoint
@app.get("/api/v1")
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "PRISM API - AI-Powered Product Management Platform",
        "docs": "/api/v1/docs",
    }


# Temporary test endpoint
@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint to verify API is working."""
    return {
        "message": "PRISM API is running!",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )