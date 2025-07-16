"""
Enhanced rate limiting middleware with DDoS protection.
Implements multiple strategies for enterprise-grade protection.
"""

import time
import hashlib
import ipaddress
import os
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from functools import wraps

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from redis import asyncio as aioredis
from pydantic import BaseModel
import jwt

from backend.src.core.config import settings
from backend.src.core.logging import logger
from backend.src.core.telemetry import trace_async, metrics

# Metrics
rate_limit_hits = metrics.counter(
    "rate_limit_hits_total",
    "Total number of rate limit hits",
    ["endpoint", "limit_type"]
)

rate_limit_requests = metrics.histogram(
    "rate_limit_requests_duration_seconds",
    "Rate limit check duration",
    ["endpoint"]
)

blocked_ips = metrics.counter(
    "blocked_ips_total",
    "Total number of blocked IPs",
    ["reason"]
)


class RateLimitConfig(BaseModel):
    """Rate limit configuration."""
    requests_per_second: int = 10
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 20
    block_duration: int = 3600  # 1 hour in seconds


class RateLimitStrategy:
    """Base rate limiting strategy."""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
    
    async def is_allowed(self, key: str, config: RateLimitConfig) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed."""
        raise NotImplementedError


class TokenBucketStrategy(RateLimitStrategy):
    """Token bucket algorithm for rate limiting."""
    
    async def is_allowed(self, key: str, config: RateLimitConfig) -> Tuple[bool, Dict[str, Any]]:
        """
        Implement token bucket algorithm.
        Allows burst traffic while maintaining average rate.
        """
        bucket_key = f"rate_limit:token_bucket:{key}"
        now = time.time()
        
        # Lua script for atomic token bucket operation
        lua_script = """
        local key = KEYS[1]
        local rate = tonumber(ARGV[1])
        local capacity = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local requested = tonumber(ARGV[4])
        
        local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
        local tokens = tonumber(bucket[1]) or capacity
        local last_update = tonumber(bucket[2]) or now
        
        -- Calculate tokens to add based on time passed
        local elapsed = math.max(0, now - last_update)
        local tokens_to_add = elapsed * rate
        tokens = math.min(capacity, tokens + tokens_to_add)
        
        -- Check if we have enough tokens
        if tokens >= requested then
            tokens = tokens - requested
            redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
            redis.call('EXPIRE', key, 3600)
            return {1, tokens, capacity}
        else
            redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
            redis.call('EXPIRE', key, 3600)
            return {0, tokens, capacity}
        end
        """
        
        result = await self.redis.eval(
            lua_script,
            1,  # number of keys
            bucket_key,
            config.requests_per_second,
            config.burst_size,
            now,
            1  # tokens requested
        )
        
        allowed = bool(result[0])
        tokens_remaining = result[1]
        capacity = result[2]
        
        headers = {
            "X-RateLimit-Limit": str(config.requests_per_minute),
            "X-RateLimit-Remaining": str(int(tokens_remaining)),
            "X-RateLimit-Reset": str(int(now + 60)),
            "X-RateLimit-Burst": str(capacity)
        }
        
        return allowed, headers


class SlidingWindowStrategy(RateLimitStrategy):
    """Sliding window algorithm for rate limiting."""
    
    async def is_allowed(self, key: str, config: RateLimitConfig) -> Tuple[bool, Dict[str, Any]]:
        """
        Implement sliding window algorithm.
        More accurate than fixed window but uses more memory.
        """
        window_key = f"rate_limit:sliding_window:{key}"
        now = time.time()
        window_start = now - 60  # 1 minute window
        
        # Remove old entries and count requests in window
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(window_key, 0, window_start)
        pipe.zadd(window_key, {str(now): now})
        pipe.zcount(window_key, window_start, now)
        pipe.expire(window_key, 120)
        
        results = await pipe.execute()
        request_count = results[2]
        
        allowed = request_count <= config.requests_per_minute
        
        headers = {
            "X-RateLimit-Limit": str(config.requests_per_minute),
            "X-RateLimit-Remaining": str(max(0, config.requests_per_minute - request_count)),
            "X-RateLimit-Reset": str(int(now + 60))
        }
        
        return allowed, headers


class DistributedRateLimiter:
    """
    Distributed rate limiter with multiple strategies and DDoS protection.
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis: Optional[aioredis.Redis] = None
        self.strategies = {}
        self.blocked_ips: Dict[str, float] = {}
        self.suspicious_patterns = []
        self._init_lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize Redis connection and strategies."""
        async with self._init_lock:
            if self.redis is None:
                try:
                    # Use Upstash REST URL if available
                    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
                    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
                    
                    if upstash_url and upstash_token:
                        # For Upstash, construct Redis URL from REST credentials
                        # Extract host from REST URL
                        import re
                        match = re.search(r'https://([^.]+)\.upstash\.io', upstash_url)
                        if match:
                            host = f"{match.group(1)}.upstash.io"
                            # Use rediss:// for SSL connection
                            redis_url = f"rediss://default:{upstash_token}@{host}:6379"
                        else:
                            redis_url = str(self.redis_url)
                    else:
                        redis_url = str(self.redis_url)
                    
                    # Convert redis:// to rediss:// for Upstash SSL connections
                    if "upstash" in redis_url and redis_url.startswith("redis://"):
                        redis_url = redis_url.replace("redis://", "rediss://", 1)
                    
                    self.redis = await aioredis.from_url(
                        redis_url,
                        encoding="utf-8",
                        decode_responses=True
                    )
                except Exception as e:
                    logger.error(f"Failed to connect to Redis: {e}")
                    logger.warning("Rate limiting disabled due to Redis connection failure")
                    # Continue without Redis - rate limiting will be disabled
                    return
                
                # Initialize strategies
                self.strategies = {
                    "token_bucket": TokenBucketStrategy(self.redis),
                    "sliding_window": SlidingWindowStrategy(self.redis)
                }
                
                # Load suspicious patterns for DDoS detection
                self.suspicious_patterns = await self._load_suspicious_patterns()
    
    async def _load_suspicious_patterns(self) -> List[Dict[str, Any]]:
        """Load patterns that might indicate DDoS attacks."""
        return [
            {"path_pattern": r"/api/v1/auth/login", "threshold": 5, "window": 60},
            {"path_pattern": r"/api/v1/auth/register", "threshold": 3, "window": 300},
            {"path_pattern": r"/api/v1/ai/generate", "threshold": 10, "window": 3600},
            {"user_agent_pattern": r"^$", "threshold": 50, "window": 60},  # Empty user agent
            {"user_agent_pattern": r"bot|crawler|spider", "threshold": 20, "window": 60}
        ]
    
    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique client identifier for rate limiting.
        Uses combination of IP, user ID, and API key.
        """
        identifiers = []
        
        # IP address (considering X-Forwarded-For for proxies)
        ip = request.client.host
        if forwarded_for := request.headers.get("X-Forwarded-For"):
            ip = forwarded_for.split(",")[0].strip()
        identifiers.append(f"ip:{ip}")
        
        # Authenticated user ID
        if hasattr(request.state, "user") and request.state.user:
            identifiers.append(f"user:{request.state.user.id}")
        
        # API key
        if api_key := request.headers.get("X-API-Key"):
            identifiers.append(f"api_key:{api_key[:8]}")
        
        return ":".join(identifiers)
    
    async def _check_ddos_patterns(self, request: Request) -> bool:
        """
        Check for DDoS attack patterns.
        Returns True if request seems suspicious.
        """
        # Check for blocked IPs
        client_ip = self._get_client_ip(request)
        if client_ip in self.blocked_ips:
            if time.time() < self.blocked_ips[client_ip]:
                blocked_ips.labels(reason="ip_blocked").inc()
                return True
            else:
                del self.blocked_ips[client_ip]
        
        # Check suspicious patterns
        for pattern in self.suspicious_patterns:
            if await self._matches_pattern(request, pattern):
                logger.warning(
                    f"Suspicious pattern detected",
                    extra={
                        "ip": client_ip,
                        "pattern": pattern,
                        "path": request.url.path
                    }
                )
                blocked_ips.labels(reason="suspicious_pattern").inc()
                return True
        
        # Check for IP reputation
        if await self._check_ip_reputation(client_ip):
            blocked_ips.labels(reason="bad_reputation").inc()
            return True
        
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP considering proxies."""
        if forwarded_for := request.headers.get("X-Forwarded-For"):
            return forwarded_for.split(",")[0].strip()
        if real_ip := request.headers.get("X-Real-IP"):
            return real_ip
        return request.client.host
    
    async def _matches_pattern(self, request: Request, pattern: Dict[str, Any]) -> bool:
        """Check if request matches suspicious pattern."""
        import re
        
        # Check path pattern
        if "path_pattern" in pattern:
            if re.search(pattern["path_pattern"], request.url.path):
                key = f"ddos_pattern:{pattern['path_pattern']}:{self._get_client_ip(request)}"
                count = await self.redis.incr(key)
                await self.redis.expire(key, pattern["window"])
                
                if count > pattern["threshold"]:
                    return True
        
        # Check user agent pattern
        if "user_agent_pattern" in pattern:
            user_agent = request.headers.get("User-Agent", "")
            if re.search(pattern["user_agent_pattern"], user_agent, re.I):
                key = f"ddos_ua_pattern:{self._get_client_ip(request)}"
                count = await self.redis.incr(key)
                await self.redis.expire(key, pattern["window"])
                
                if count > pattern["threshold"]:
                    return True
        
        return False
    
    async def _check_ip_reputation(self, ip: str) -> bool:
        """
        Check IP reputation against threat intelligence.
        In production, integrate with services like AbuseIPDB, IPQualityScore, etc.
        """
        # Check if IP is in private range (development)
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback:
                return False
        except ValueError:
            return True
        
        # Check Redis cache for known bad IPs
        bad_ip_key = f"bad_ip:{ip}"
        if await self.redis.exists(bad_ip_key):
            return True
        
        # In production, make API call to threat intelligence service
        # For now, return False
        return False
    
    def _get_rate_limit_config(self, request: Request) -> RateLimitConfig:
        """
        Get rate limit configuration based on endpoint and user type.
        """
        path = request.url.path
        
        # Different limits for different endpoints
        if path.startswith("/api/v1/auth/"):
            return RateLimitConfig(
                requests_per_second=2,
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=500,
                burst_size=5
            )
        elif path.startswith("/api/v1/ai/"):
            return RateLimitConfig(
                requests_per_second=1,
                requests_per_minute=5,
                requests_per_hour=50,
                requests_per_day=200,
                burst_size=3
            )
        elif path.startswith("/api/v1/public/"):
            return RateLimitConfig(
                requests_per_second=20,
                requests_per_minute=200,
                requests_per_hour=2000,
                requests_per_day=20000,
                burst_size=50
            )
        
        # Default limits
        config = RateLimitConfig()
        
        # Higher limits for authenticated users
        if hasattr(request.state, "user") and request.state.user:
            config.requests_per_minute *= 2
            config.requests_per_hour *= 2
            config.requests_per_day *= 2
            config.burst_size *= 2
        
        return config
    
    @trace_async("rate_limit_check")
    async def check_rate_limit(self, request: Request) -> Optional[JSONResponse]:
        """
        Check if request should be rate limited.
        Returns JSONResponse if limited, None if allowed.
        """
        # Initialize if needed
        if self.redis is None:
            await self.initialize()
        
        # If Redis is still not available after initialization, skip rate limiting
        if self.redis is None:
            logger.debug("Rate limiting skipped - Redis not available")
            return None
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return None
        
        # Check for DDoS patterns first
        if await self._check_ddos_patterns(request):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too many requests",
                    "message": "Your IP has been temporarily blocked due to suspicious activity",
                    "retry_after": 3600
                },
                headers={
                    "Retry-After": "3600",
                    "X-RateLimit-Blocked": "true"
                }
            )
        
        # Get client identifier and config
        client_id = self._get_client_identifier(request)
        config = self._get_rate_limit_config(request)
        
        # Use token bucket strategy by default
        strategy = self.strategies.get("token_bucket")
        if not strategy:
            logger.error("No rate limit strategy available")
            return None
        
        # Check rate limit
        with rate_limit_requests.labels(endpoint=request.url.path).time():
            allowed, headers = await strategy.is_allowed(client_id, config)
        
        if not allowed:
            rate_limit_hits.labels(
                endpoint=request.url.path,
                limit_type="token_bucket"
            ).inc()
            
            # Log rate limit hit
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "client_id": client_id,
                    "endpoint": request.url.path,
                    "limit": config.requests_per_minute
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too many requests",
                    "message": f"Rate limit exceeded. Please retry after {headers.get('X-RateLimit-Reset', 'unknown')}",
                    "retry_after": int(headers.get("X-RateLimit-Reset", 60))
                },
                headers=headers
            )
        
        # Add rate limit headers to request for later use
        request.state.rate_limit_headers = headers
        return None


# Global rate limiter instance
rate_limiter = DistributedRateLimiter()


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Check rate limit
            if response := await rate_limiter.check_rate_limit(request):
                await response(scope, receive, send)
                return
            
            # Add rate limit headers to response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    # Add rate limit headers if available
                    if hasattr(request.state, "rate_limit_headers"):
                        for key, value in request.state.rate_limit_headers.items():
                            headers[key.encode()] = value.encode()
                    
                    message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


def rate_limit(
    requests_per_minute: int = 60,
    requests_per_hour: int = 600,
    strategy: str = "token_bucket"
):
    """
    Decorator for custom rate limiting on specific endpoints.
    
    Usage:
        @router.get("/expensive-operation")
        @rate_limit(requests_per_minute=10)
        async def expensive_operation():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Create custom config
            config = RateLimitConfig(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour
            )
            
            # Get strategy
            if rate_limiter.redis is None:
                await rate_limiter.initialize()
            
            limiter_strategy = rate_limiter.strategies.get(strategy)
            if not limiter_strategy:
                raise ValueError(f"Unknown rate limit strategy: {strategy}")
            
            # Check rate limit
            client_id = rate_limiter._get_client_identifier(request)
            allowed, headers = await limiter_strategy.is_allowed(client_id, config)
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers=headers
                )
            
            # Add headers to response
            response = await func(request, *args, **kwargs)
            for key, value in headers.items():
                response.headers[key] = value
            
            return response
        
        return wrapper
    return decorator