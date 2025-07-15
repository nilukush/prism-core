"""
Redis cache configuration and utilities.
Provides caching functionality for the application.
"""

import json
from typing import Any, Optional, Union

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Redis cache manager with async support."""
    
    def __init__(self) -> None:
        """Initialize Redis cache manager."""
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._pool = ConnectionPool.from_url(
                str(settings.REDIS_URL),
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                max_connections=settings.REDIS_POOL_SIZE,
            )
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            logger.info("redis_connected", url=str(settings.REDIS_URL))
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
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
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
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
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
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Success status
        """
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
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            Existence status
        """
        if not self._client:
            return False
        
        try:
            return bool(await self._client.exists(key))
        except Exception as e:
            logger.error("cache_exists_error", key=key, error=str(e))
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        if not self._client:
            logger.warning("redis_not_connected")
            return 0
        
        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error("cache_clear_pattern_error", pattern=pattern, error=str(e))
            return 0
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter in cache.
        
        Args:
            key: Counter key
            amount: Increment amount
            
        Returns:
            New counter value
        """
        if not self._client:
            logger.warning("redis_not_connected")
            return None
        
        try:
            return await self._client.incrby(key, amount)
        except Exception as e:
            logger.error("cache_increment_error", key=key, error=str(e))
            return None
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs
        """
        if not self._client:
            logger.warning("redis_not_connected")
            return {}
        
        try:
            values = await self._client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            logger.error("cache_get_many_error", keys=keys, error=str(e))
            return {}
    
    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set multiple values in cache.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
        if not self._client:
            logger.warning("redis_not_connected")
            return False
        
        try:
            # Serialize all values
            serialized_mapping = {
                key: json.dumps(value) for key, value in mapping.items()
            }
            
            if ttl:
                # Use pipeline for atomic operation with TTL
                pipe = self._client.pipeline()
                for key, value in serialized_mapping.items():
                    pipe.setex(key, ttl, value)
                await pipe.execute()
            else:
                await self._client.mset(serialized_mapping)
            
            return True
        except Exception as e:
            logger.error("cache_set_many_error", error=str(e))
            return False


# Global cache instance
cache = RedisCache()


# Cache key generators
def generate_cache_key(*parts: Union[str, int]) -> str:
    """
    Generate cache key from parts.
    
    Args:
        *parts: Key parts
        
    Returns:
        Cache key
    """
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