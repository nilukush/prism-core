"""
Redis-backed refresh token store for production use.
Provides persistent storage for refresh token families across server restarts.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from redis import asyncio as aioredis
import asyncio

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class RedisRefreshTokenStore:
    """Redis-backed store for managing refresh token families."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis: Optional[aioredis.Redis] = None
        self._prefix = "refresh_token:family:"
        self._ttl = 30 * 24 * 60 * 60  # 30 days
    
    async def initialize(self):
        """Initialize Redis connection."""
        if not self.redis:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def create_family(self, user_id: int) -> str:
        """Create a new token family."""
        import uuid
        family_id = str(uuid.uuid4())
        
        family_data = {
            "user_id": user_id,
            "current_token_id": None,
            "used_tokens": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_rotation": datetime.now(timezone.utc).isoformat()
        }
        
        key = f"{self._prefix}{family_id}"
        await self.redis.setex(key, self._ttl, json.dumps(family_data))
        
        return family_id
    
    async def add_token(self, family_id: str, token_id: str) -> None:
        """Add token to family."""
        key = f"{self._prefix}{family_id}"
        
        # Get existing family data
        data = await self.redis.get(key)
        if not data:
            return
        
        family = json.loads(data)
        
        # Add current token to used tokens
        if family["current_token_id"]:
            family["used_tokens"].append(family["current_token_id"])
            # Keep only last 10 used tokens to prevent unbounded growth
            family["used_tokens"] = family["used_tokens"][-10:]
        
        family["current_token_id"] = token_id
        family["last_rotation"] = datetime.now(timezone.utc).isoformat()
        
        # Update in Redis
        await self.redis.setex(key, self._ttl, json.dumps(family))
    
    async def validate_token(self, family_id: str, token_id: str) -> bool:
        """Validate token and detect reuse."""
        key = f"{self._prefix}{family_id}"
        
        # Get family data
        data = await self.redis.get(key)
        if not data:
            return False
        
        family = json.loads(data)
        
        # Check if token was already used
        if token_id in family["used_tokens"]:
            # Check for race condition (within 5 seconds)
            last_rotation = datetime.fromisoformat(family["last_rotation"])
            if (datetime.now(timezone.utc) - last_rotation).total_seconds() < 5:
                logger.info(
                    "refresh_token_race_condition_detected",
                    family_id=family_id,
                    token_id=token_id,
                    user_id=family["user_id"]
                )
                return family["current_token_id"] == token_id
            
            # Token reuse detected - invalidate family
            logger.warning(
                "refresh_token_reuse_detected",
                family_id=family_id,
                token_id=token_id,
                user_id=family["user_id"]
            )
            await self.redis.delete(key)
            return False
        
        # Check if token is current
        return family["current_token_id"] == token_id
    
    async def get_user_id(self, family_id: str) -> Optional[int]:
        """Get user ID for token family."""
        key = f"{self._prefix}{family_id}"
        data = await self.redis.get(key)
        
        if data:
            family = json.loads(data)
            return family["user_id"]
        
        return None
    
    async def revoke_family(self, family_id: str) -> None:
        """Revoke entire token family."""
        key = f"{self._prefix}{family_id}"
        await self.redis.delete(key)
    
    async def revoke_user_families(self, user_id: int) -> None:
        """Revoke all token families for a user."""
        # Scan for all families belonging to the user
        pattern = f"{self._prefix}*"
        
        async for key in self.redis.scan_iter(match=pattern):
            data = await self.redis.get(key)
            if data:
                family = json.loads(data)
                if family["user_id"] == user_id:
                    await self.redis.delete(key)
    
    async def cleanup_expired(self) -> None:
        """Clean up expired token families."""
        # Redis handles expiration automatically with TTL
        pass


# Global instance for production use
if settings.ENVIRONMENT == "production":
    redis_refresh_token_store = RedisRefreshTokenStore()
else:
    # Use in-memory store for development
    redis_refresh_token_store = None