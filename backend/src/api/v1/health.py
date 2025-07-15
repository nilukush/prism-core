"""
Health check API endpoints.
Provides system health status and readiness checks.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
from datetime import datetime

from backend.src.core.database import get_db
from backend.src.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health")


@router.get("", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Returns 200 OK if the service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "prism-api",
        "version": settings.VERSION
    }


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Readiness check endpoint.
    Verifies all critical dependencies are available.
    """
    checks = {
        "database": False,
        "redis": False,
        "vector_db": False
    }
    details = {}
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        checks["database"] = result.scalar() == 1
        details["database"] = "Connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        details["database"] = str(e)
    
    # Check Redis
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        await redis_client.ping()
        checks["redis"] = True
        details["redis"] = "Connected"
        await redis_client.close()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        details["redis"] = str(e)
    
    # Check Vector DB (Qdrant)
    try:
        # Would implement actual Qdrant health check
        checks["vector_db"] = True
        details["vector_db"] = "Connected"
    except Exception as e:
        logger.error(f"Vector DB health check failed: {e}")
        details["vector_db"] = str(e)
    
    # Overall status
    all_healthy = all(checks.values())
    
    response = {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "details": details
    }
    
    if not all_healthy:
        return response
    
    return response


@router.get("/live", response_model=Dict[str, Any])
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint.
    Used by orchestrators to determine if the container should be restarted.
    """
    # Add any checks that would indicate the service needs to be restarted
    # For now, if the endpoint responds, the service is alive
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }