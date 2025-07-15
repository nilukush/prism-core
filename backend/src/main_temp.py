"""
Temporary simplified FastAPI application for PRISM.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Basic configuration
class Settings:
    PROJECT_NAME = "PRISM"
    VERSION = "0.1.0"
    APP_ENV = "development"
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3100"]

settings = Settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting PRISM API...")
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
try:
    from backend.src.api.v1.router import api_v1_router
    app.include_router(api_v1_router, prefix="/api/v1")
except Exception as e:
    logger.error(f"Could not import API router: {e}")

# Add simple AI router for testing
try:
    from backend.src.api.v1.ai_simple import router as ai_simple_router
    app.include_router(ai_simple_router, prefix="/api/v1/ai", tags=["ai"])
    logger.info("AI simple router loaded")
except Exception as e:
    logger.error(f"Could not import AI simple router: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "prism-api"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to PRISM API",
        "version": settings.VERSION,
        "docs": "/api/v1/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)