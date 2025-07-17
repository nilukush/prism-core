"""
Upstash Redis adapter for PRISM
Provides compatibility layer between Upstash REST API and standard Redis interface
"""

import json
import httpx
from typing import Optional, Any, Dict, List
from urllib.parse import quote
import asyncio
from functools import wraps

from backend.src.core.config import settings


class UpstashRedis:
    """
    Upstash Redis REST API client
    Provides Redis-like interface for Upstash's REST API
    """
    
    def __init__(self, url: str, token: str):
        self.base_url = url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def _request(self, command: List[str]) -> Any:
        """Execute a Redis command via Upstash REST API"""
        try:
            # Upstash expects commands as array
            response = await self._client.post(
                self.base_url,
                json=command,
                headers=self.headers
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("result")
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise Exception("Upstash rate limit exceeded")
            raise
        except Exception as e:
            print(f"Upstash Redis error: {e}")
            raise
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        result = await self._request(["GET", key])
        return result
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set key-value with optional expiration"""
        command = ["SET", key, value]
        if ex:
            command.extend(["EX", str(ex)])
        
        result = await self._request(command)
        return result == "OK"
    
    async def delete(self, key: str) -> int:
        """Delete key"""
        result = await self._request(["DEL", key])
        return result
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        result = await self._request(["EXISTS", key])
        return bool(result)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        result = await self._request(["EXPIRE", key, str(seconds)])
        return bool(result)
    
    async def ttl(self, key: str) -> int:
        """Get key TTL"""
        result = await self._request(["TTL", key])
        return result
    
    async def incr(self, key: str) -> int:
        """Increment counter"""
        result = await self._request(["INCR", key])
        return result
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field value"""
        result = await self._request(["HGET", key, field])
        return result
    
    async def hset(self, key: str, field: str, value: str) -> int:
        """Set hash field value"""
        result = await self._request(["HSET", key, field, value])
        return result
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields and values"""
        result = await self._request(["HGETALL", key])
        if not result:
            return {}
        
        # Convert flat array to dict
        return {result[i]: result[i+1] for i in range(0, len(result), 2)}
    
    async def sadd(self, key: str, *members: str) -> int:
        """Add members to set"""
        command = ["SADD", key] + list(members)
        result = await self._request(command)
        return result
    
    async def srem(self, key: str, *members: str) -> int:
        """Remove members from set"""
        command = ["SREM", key] + list(members)
        result = await self._request(command)
        return result
    
    async def smembers(self, key: str) -> List[str]:
        """Get all set members"""
        result = await self._request(["SMEMBERS", key])
        return result or []
    
    async def sismember(self, key: str, member: str) -> bool:
        """Check if member exists in set"""
        result = await self._request(["SISMEMBER", key, member])
        return bool(result)
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        result = await self._request(["KEYS", pattern])
        return result or []
    
    async def flushdb(self) -> bool:
        """Clear all keys (use with caution)"""
        result = await self._request(["FLUSHDB"])
        return result == "OK"
    
    async def ping(self) -> bool:
        """Test connection"""
        result = await self._request(["PING"])
        return result == "PONG"
    
    async def close(self):
        """Close the HTTP client"""
        await self._client.aclose()


def get_redis_client() -> Optional[UpstashRedis]:
    """
    Get Redis client instance
    Returns Upstash client for free tier deployment
    """
    # Check if using Upstash
    if hasattr(settings, 'UPSTASH_REDIS_REST_URL') and settings.UPSTASH_REDIS_REST_URL:
        return UpstashRedis(
            url=settings.UPSTASH_REDIS_REST_URL,
            token=settings.UPSTASH_REDIS_REST_TOKEN
        )
    
    # Fallback to standard Redis URL parsing
    if settings.REDIS_URL:
        # For local development with standard Redis
        # You can add standard redis client here if needed
        return None
    
    return None


# Singleton instance
_redis_client: Optional[UpstashRedis] = None


async def get_redis() -> Optional[UpstashRedis]:
    """Get or create Redis client instance"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = get_redis_client()
    
    return _redis_client


# Helper decorators for caching
def redis_cache(key_prefix: str, ttl: int = 3600):
    """
    Decorator for caching function results in Redis
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis = await get_redis()
            if not redis:
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = f"{key_prefix}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            try:
                cached = await redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            try:
                await redis.set(
                    cache_key,
                    json.dumps(result, default=str),
                    ex=ttl
                )
            except Exception:
                pass
            
            return result
        
        return wrapper
    return decorator