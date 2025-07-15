"""
Rate limiting middleware.
"""

import time
from typing import Callable, Dict, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.src.core.config import settings
from backend.src.core.cache import cache
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window."""
    
    def __init__(self, app, default_limit: int = None, window: int = None):
        super().__init__(app)
        self.default_limit = default_limit or settings.RATE_LIMIT_DEFAULT
        self.window = window or settings.RATE_LIMIT_WINDOW
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits before processing request."""
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)
        
        # Get client identifier (IP address or user ID)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        allowed, limit_info = await self._check_rate_limit(client_id, request.url.path)
        
        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                path=request.url.path,
                limit=limit_info["limit"],
                window=limit_info["window"],
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": limit_info["retry_after"],
                },
                headers={
                    "X-RateLimit-Limit": str(limit_info["limit"]),
                    "X-RateLimit-Remaining": str(limit_info["remaining"]),
                    "X-RateLimit-Reset": str(limit_info["reset"]),
                    "Retry-After": str(limit_info["retry_after"]),
                },
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(limit_info["reset"])
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try to get authenticated user ID
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    async def _check_rate_limit(
        self,
        client_id: str,
        path: str,
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is within rate limits.
        
        Returns:
            Tuple of (allowed, limit_info)
        """
        # Get endpoint-specific limit or use default
        limit = self._get_endpoint_limit(path)
        
        # Generate cache key
        window_start = int(time.time()) // self.window * self.window
        cache_key = f"rate_limit:{client_id}:{window_start}"
        
        # Get current count
        current_count = await cache.get(cache_key) or 0
        
        # Check if limit exceeded
        if current_count >= limit:
            remaining = 0
            allowed = False
        else:
            # Increment counter
            new_count = await cache.increment(cache_key)
            if new_count == 1:
                # First request in window, set TTL
                await cache.set(cache_key, 1, ttl=self.window)
            
            remaining = max(0, limit - new_count)
            allowed = new_count <= limit
        
        # Calculate reset time
        reset_time = window_start + self.window
        retry_after = reset_time - int(time.time())
        
        return allowed, {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": retry_after,
            "window": self.window,
        }
    
    def _get_endpoint_limit(self, path: str) -> int:
        """Get rate limit for specific endpoint."""
        # Define endpoint-specific limits
        endpoint_limits = {
            "/api/v1/ai/generate": 50,  # AI endpoints have lower limits
            "/api/v1/auth/login": 10,    # Auth endpoints have strict limits
            "/api/v1/auth/register": 5,
        }
        
        # Check for exact match
        for endpoint, limit in endpoint_limits.items():
            if path.startswith(endpoint):
                return limit
        
        # Return default limit
        return self.default_limit