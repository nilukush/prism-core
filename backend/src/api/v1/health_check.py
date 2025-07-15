"""
Comprehensive health check endpoints for monitoring.
Implements health checks for all critical components.
"""

import time
import psutil
import os
from typing import Dict, Any, List
from datetime import datetime, timezone
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import redis.asyncio as redis

from backend.src.api.deps import get_db, get_current_user
from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.models.user import User
from backend.src.core.telemetry import record_metric

logger = get_logger(__name__)
router = APIRouter()


class HealthStatus:
    """Health status constants."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth:
    """Component health check result."""
    
    def __init__(
        self,
        name: str,
        status: str,
        latency_ms: float,
        details: Dict[str, Any] = None,
        error: str = None
    ):
        self.name = name
        self.status = status
        self.latency_ms = latency_ms
        self.details = details or {}
        self.error = error
        self.checked_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "status": self.status,
            "latency_ms": round(self.latency_ms, 2),
            "checked_at": self.checked_at
        }
        
        if self.details:
            result["details"] = self.details
        
        if self.error:
            result["error"] = self.error
        
        return result


class HealthChecker:
    """Health check service."""
    
    @staticmethod
    async def check_database(db: AsyncSession) -> ComponentHealth:
        """Check database connectivity and performance."""
        start_time = time.time()
        
        try:
            # Basic connectivity check
            result = await db.execute(text("SELECT 1"))
            result.scalar()
            
            # Get database statistics
            stats_query = text("""
                SELECT 
                    (SELECT count(*) FROM pg_stat_activity) as connections,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle') as idle_connections,
                    pg_database_size(current_database()) as database_size
            """)
            
            stats_result = await db.execute(stats_query)
            stats = stats_result.fetchone()
            
            # Get table counts
            table_counts_query = text("""
                SELECT 
                    (SELECT count(*) FROM users) as users,
                    (SELECT count(*) FROM projects) as projects,
                    (SELECT count(*) FROM stories) as stories,
                    (SELECT count(*) FROM organizations) as organizations
            """)
            
            counts_result = await db.execute(table_counts_query)
            counts = counts_result.fetchone()
            
            latency = (time.time() - start_time) * 1000
            
            # Check if performance is degraded
            status = HealthStatus.HEALTHY
            if latency > 100:  # More than 100ms is concerning
                status = HealthStatus.DEGRADED
            
            return ComponentHealth(
                name="database",
                status=status,
                latency_ms=latency,
                details={
                    "connections": {
                        "total": stats.connections,
                        "active": stats.active_queries,
                        "idle": stats.idle_connections
                    },
                    "size_bytes": stats.database_size,
                    "size_human": f"{stats.database_size / 1024 / 1024:.2f} MB",
                    "table_counts": {
                        "users": counts.users,
                        "projects": counts.projects,
                        "stories": counts.stories,
                        "organizations": counts.organizations
                    }
                }
            )
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            logger.error("database_health_check_failed", error=str(e))
            
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                error=str(e)
            )
    
    @staticmethod
    async def check_redis() -> ComponentHealth:
        """Check Redis connectivity and performance."""
        start_time = time.time()
        
        try:
            # Parse Redis URL
            redis_url = settings.REDIS_URL
            if isinstance(redis_url, str):
                client = redis.from_url(redis_url, decode_responses=True)
            else:
                client = redis.from_url(str(redis_url), decode_responses=True)
            
            # Ping Redis
            await client.ping()
            
            # Get Redis info
            info = await client.info()
            memory_info = await client.info("memory")
            
            # Get some key statistics
            db_size = await client.dbsize()
            
            await client.close()
            
            latency = (time.time() - start_time) * 1000
            
            # Check if performance is degraded
            status = HealthStatus.HEALTHY
            if latency > 50:  # More than 50ms is concerning for Redis
                status = HealthStatus.DEGRADED
            
            return ComponentHealth(
                name="redis",
                status=status,
                latency_ms=latency,
                details={
                    "version": info.get("redis_version", "unknown"),
                    "uptime_seconds": info.get("uptime_in_seconds", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": memory_info.get("used_memory_human", "0B"),
                    "used_memory_bytes": memory_info.get("used_memory", 0),
                    "keys": db_size,
                    "role": info.get("role", "unknown")
                }
            )
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            logger.error("redis_health_check_failed", error=str(e))
            
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                error=str(e)
            )
    
    @staticmethod
    async def check_external_services() -> List[ComponentHealth]:
        """Check external service connectivity."""
        services = []
        
        # TEMPORARILY DISABLED TO PREVENT API COSTS
        # These health checks were making actual API calls to OpenAI/Anthropic
        # which can result in unexpected costs if called frequently
        
        # # Check OpenAI API
        # if settings.OPENAI_API_KEY:
        #     services.append(await HealthChecker._check_openai())
        
        # # Check Anthropic API
        # if settings.ANTHROPIC_API_KEY:
        #     services.append(await HealthChecker._check_anthropic())
        
        # Instead, add configuration-only checks that don't make API calls
        if settings.OPENAI_API_KEY:
            services.append(ComponentHealth(
                name="openai",
                status=HealthStatus.HEALTHY if settings.OPENAI_API_KEY.startswith("sk-") else HealthStatus.DEGRADED,
                latency_ms=0,
                details={"configured": True, "check_type": "config_only"}
            ))
        
        if settings.ANTHROPIC_API_KEY:
            services.append(ComponentHealth(
                name="anthropic",
                status=HealthStatus.HEALTHY if settings.ANTHROPIC_API_KEY.startswith("sk-ant-") else HealthStatus.DEGRADED,
                latency_ms=0,
                details={"configured": True, "check_type": "config_only"}
            ))
        
        # Check email service
        services.append(await HealthChecker._check_email_service())
        
        # Check Qdrant if configured
        if settings.QDRANT_URL:
            services.append(await HealthChecker._check_qdrant())
        
        return services
    
    @staticmethod
    async def _check_openai() -> ComponentHealth:
        """Check OpenAI API connectivity."""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    timeout=5.0
                )
                
                latency = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    models = response.json()
                    return ComponentHealth(
                        name="openai",
                        status=HealthStatus.HEALTHY,
                        latency_ms=latency,
                        details={
                            "available_models": len(models.get("data", [])),
                            "status_code": response.status_code
                        }
                    )
                else:
                    return ComponentHealth(
                        name="openai",
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=latency,
                        error=f"API returned status {response.status_code}"
                    )
                    
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="openai",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                error=str(e)
            )
    
    @staticmethod
    async def _check_email_service() -> ComponentHealth:
        """Check email service connectivity."""
        start_time = time.time()
        
        try:
            # For SMTP, we'll just check if we can connect
            if settings.EMAIL_PROVIDER == "smtp":
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((settings.SMTP_HOST, settings.SMTP_PORT))
                sock.close()
                
                latency = (time.time() - start_time) * 1000
                
                if result == 0:
                    return ComponentHealth(
                        name="email_service",
                        status=HealthStatus.HEALTHY,
                        latency_ms=latency,
                        details={
                            "provider": settings.EMAIL_PROVIDER,
                            "host": settings.SMTP_HOST,
                            "port": settings.SMTP_PORT
                        }
                    )
                else:
                    return ComponentHealth(
                        name="email_service",
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=latency,
                        error="Cannot connect to SMTP server"
                    )
            
            # For other providers, return basic info
            latency = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="email_service",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                details={
                    "provider": settings.EMAIL_PROVIDER,
                    "enabled": settings.EMAIL_ENABLED
                }
            )
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="email_service",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                error=str(e)
            )
    
    @staticmethod
    async def _check_anthropic() -> ComponentHealth:
        """Check Anthropic API connectivity."""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": settings.ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01"
                    },
                    timeout=5.0
                )
                
                latency = (time.time() - start_time) * 1000
                
                if response.status_code in [200, 401]:  # 401 means API key issue, not connectivity
                    return ComponentHealth(
                        name="anthropic",
                        status=HealthStatus.HEALTHY if response.status_code == 200 else HealthStatus.DEGRADED,
                        latency_ms=latency,
                        details={"status_code": response.status_code}
                    )
                else:
                    return ComponentHealth(
                        name="anthropic",
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=latency,
                        error=f"API returned status {response.status_code}"
                    )
                    
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="anthropic",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                error=str(e)
            )
    
    @staticmethod
    async def _check_qdrant() -> ComponentHealth:
        """Check Qdrant vector database connectivity."""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if settings.QDRANT_API_KEY:
                    headers["api-key"] = settings.QDRANT_API_KEY
                
                response = await client.get(
                    f"{settings.QDRANT_URL}/collections",
                    headers=headers,
                    timeout=5.0
                )
                
                latency = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    return ComponentHealth(
                        name="qdrant",
                        status=HealthStatus.HEALTHY,
                        latency_ms=latency,
                        details={
                            "collections": len(data.get("result", {}).get("collections", [])),
                            "status_code": response.status_code
                        }
                    )
                else:
                    return ComponentHealth(
                        name="qdrant",
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=latency,
                        error=f"API returned status {response.status_code}"
                    )
                    
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="qdrant",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                error=str(e)
            )


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns 200 OK if the service is running.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Returns 200 OK if the service is alive.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint.
    
    Checks if the service is ready to handle requests.
    """
    try:
        # Quick database check
        await db.execute(text("SELECT 1"))
        
        # Quick Redis check
        redis_url = settings.REDIS_URL
        if isinstance(redis_url, str):
            client = redis.from_url(redis_url)
        else:
            client = redis.from_url(str(redis_url))
        
        await client.ping()
        await client.close()
        
        return {"status": "ready"}
        
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/health/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detailed health check for monitoring systems.
    
    Requires authentication and admin role.
    """
    # Check if user is admin
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Run all health checks concurrently
    results = await asyncio.gather(
        HealthChecker.check_database(db),
        HealthChecker.check_redis(),
        HealthChecker.check_external_services(),
        return_exceptions=True
    )
    
    # Process results
    components = []
    external_services = []
    
    for result in results:
        if isinstance(result, Exception):
            components.append(ComponentHealth(
                name="unknown",
                status=HealthStatus.UNHEALTHY,
                latency_ms=0,
                error=str(result)
            ))
        elif isinstance(result, list):
            external_services.extend(result)
        else:
            components.append(result)
    
    # Add external services to components
    components.extend(external_services)
    
    # Calculate overall status
    statuses = [comp.status for comp in components]
    if all(s == HealthStatus.HEALTHY for s in statuses):
        overall_status = HealthStatus.HEALTHY
    elif any(s == HealthStatus.UNHEALTHY for s in statuses):
        overall_status = HealthStatus.UNHEALTHY
    else:
        overall_status = HealthStatus.DEGRADED
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get process metrics
    process = psutil.Process(os.getpid())
    process_memory = process.memory_info()
    
    # Record metrics
    record_metric("health_check.performed", 1, "counter", {"type": "detailed"})
    
    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV
        },
        "components": [comp.to_dict() for comp in components],
        "system": {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "used_bytes": memory.used,
                "percent": memory.percent
            },
            "disk": {
                "total_bytes": disk.total,
                "used_bytes": disk.used,
                "free_bytes": disk.free,
                "percent": disk.percent
            },
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        },
        "process": {
            "memory_bytes": process_memory.rss,
            "memory_mb": round(process_memory.rss / 1024 / 1024, 2),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections())
        }
    }


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format.
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    metrics = generate_latest()
    
    return Response(
        content=metrics,
        media_type=CONTENT_TYPE_LATEST
    )