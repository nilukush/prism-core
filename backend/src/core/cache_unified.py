"""
Unified Redis cache configuration that supports both standard Redis and Upstash.
Automatically detects and uses Upstash when configured.
"""

import json
import os
from typing import Any, Optional, Union
from abc import ABC, abstractmethod

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class CacheInterface(ABC):
    """Abstract interface for cache implementations."""
    
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        pass


class UpstashCache(CacheInterface):
    """Upstash Redis cache implementation."""
    
    def __init__(self):
        from backend.src.core.redis_upstash import UpstashRedis
        self.url = settings.UPSTASH_REDIS_REST_URL
        self.token = settings.UPSTASH_REDIS_REST_TOKEN
        self._client: Optional[UpstashRedis] = None
    
    async def connect(self) -> None:
        """Connect to Upstash Redis."""
        try:
            from backend.src.core.redis_upstash import UpstashRedis
            self._client = UpstashRedis(self.url, self.token)
            # Test connection
            await self._client.ping()
            logger.info("upstash_redis_connected", url=self.url)
        except Exception as e:
            logger.error("upstash_redis_connection_failed", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Upstash Redis."""
        if self._client:
            await self._client.close()
        logger.info("upstash_redis_disconnected")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._client:
            logger.warning("upstash_redis_not_connected")
            return None
        
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self._client:
            logger.warning("upstash_redis_not_connected")
            return False
        
        try:
            serialized = json.dumps(value)
            result = await self._client.set(key, serialized, ex=ttl)
            return result
        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._client:
            logger.warning("upstash_redis_not_connected")
            return False
        
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error("cache_delete_error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._client:
            return False
        
        try:
            return await self._client.exists(key)
        except Exception as e:
            logger.error("cache_exists_error", key=key, error=str(e))
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache."""
        if not self._client:
            logger.warning("upstash_redis_not_connected")
            return None
        
        try:
            # Upstash doesn't have incrby, so we use incr multiple times
            result = None
            for _ in range(amount):
                result = await self._client.incr(key)
            return result
        except Exception as e:
            logger.error("cache_increment_error", key=key, error=str(e))
            return None


class StandardRedisCache(CacheInterface):
    """Standard Redis cache implementation."""
    
    def __init__(self):
        import redis.asyncio as redis
        from redis.asyncio.connection import ConnectionPool
        
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self.redis = redis
        self.ConnectionPool = ConnectionPool
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            # Check if we should use Upstash URL format
            redis_url = str(settings.REDIS_URL)
            
            # If UPSTASH environment variables exist but we're using standard Redis
            # This might be a misconfiguration
            if settings.UPSTASH_REDIS_REST_URL and 'localhost' in redis_url:
                logger.warning("upstash_configured_but_using_localhost")
            
            self._pool = self.ConnectionPool.from_url(
                redis_url,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                max_connections=settings.REDIS_POOL_SIZE,
            )
            self._client = self.redis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            logger.info("redis_connected", url=redis_url)
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("redis_disconnected")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._client:
            logger.warning("redis_not_connected")
            return None
        
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self._client:
            logger.warning("redis_not_connected")
            return False
        
        try:
            serialized = json.dumps(value)
            if ttl:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)
            return True
        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._client:
            logger.warning("redis_not_connected")
            return False
        
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error("cache_delete_error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._client:
            return False
        
        try:
            return bool(await self._client.exists(key))
        except Exception as e:
            logger.error("cache_exists_error", key=key, error=str(e))
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache."""
        if not self._client:
            logger.warning("redis_not_connected")
            return None
        
        try:
            return await self._client.incrby(key, amount)
        except Exception as e:
            logger.error("cache_increment_error", key=key, error=str(e))
            return None


class UnifiedRedisCache:
    """
    Unified Redis cache that automatically selects between Upstash and standard Redis.
    This maintains compatibility with the existing RedisCache interface.
    """
    
    def __init__(self) -> None:
        """Initialize Redis cache manager."""
        self._implementation: Optional[CacheInterface] = None
        
    def _select_implementation(self) -> CacheInterface:
        """Select the appropriate Redis implementation based on configuration."""
        # Check if Upstash is configured
        if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
            logger.info("using_upstash_redis")
            return UpstashCache()
        else:
            logger.info("using_standard_redis")
            return StandardRedisCache()
    
    async def connect(self) -> None:
        """Connect to Redis."""
        self._implementation = self._select_implementation()
        await self._implementation.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._implementation:
            await self._implementation.disconnect()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._implementation:
            return None
        return await self._implementation.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self._implementation:
            return False
        return await self._implementation.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._implementation:
            return False
        return await self._implementation.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._implementation:
            return False
        return await self._implementation.exists(key)
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache."""
        if not self._implementation:
            return None
        return await self._implementation.increment(key, amount)
    
    # Add other methods from the original RedisCache as needed
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern - not implemented for Upstash."""
        # This is a complex operation that's not easily supported by Upstash REST API
        logger.warning("clear_pattern_not_supported")
        return 0
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache."""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    async def set_many(self, mapping: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        success = True
        for key, value in mapping.items():
            if not await self.set(key, value, ttl):
                success = False
        return success


# Global cache instance - replace the original cache
cache = UnifiedRedisCache()


# Cache key generators (keep the same as original)
def generate_cache_key(*parts: Union[str, int]) -> str:
    """Generate cache key from parts."""
    return ":".join(str(part) for part in parts)


def user_cache_key(user_id: int, suffix: str) -> str:
    """Generate user-specific cache key."""
    return generate_cache_key("user", user_id, suffix)


def document_cache_key(doc_id: int) -> str:
    """Generate document cache key."""
    return generate_cache_key("document", doc_id)


def story_cache_key(story_id: int) -> str:
    """Generate story cache key."""
    return generate_cache_key("story", story_id)


def agent_cache_key(agent_type: str, input_hash: str) -> str:
    """Generate agent result cache key."""
    return generate_cache_key("agent", agent_type, input_hash)