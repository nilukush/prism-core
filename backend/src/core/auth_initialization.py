"""
Authentication initialization module.
Handles proper setup of persistent token stores.
"""

import asyncio
from typing import Optional

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)

_redis_store_instance: Optional[Any] = None

async def initialize_auth_stores():
    """Initialize authentication stores based on configuration."""
    global _redis_store_instance
    
    use_persistent = settings.get("USE_PERSISTENT_TOKENS", "false").lower() == "true"
    
    if use_persistent and settings.ENVIRONMENT in ["production", "staging"]:
        try:
            from backend.src.services.auth_token_store import RedisRefreshTokenStore
            
            logger.info("Initializing Redis refresh token store...")
            _redis_store_instance = RedisRefreshTokenStore(settings.REDIS_URL)
            await _redis_store_instance.initialize()
            
            # Monkey-patch the auth module to use Redis store
            import backend.src.services.auth as auth_module
            auth_module.refresh_token_store = _redis_store_instance
            
            logger.info("Successfully initialized Redis token store")
            return _redis_store_instance
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis token store: {e}")
            logger.warning("Falling back to in-memory token store")
    
    else:
        logger.info(
            f"Using in-memory token store "
            f"(USE_PERSISTENT_TOKENS={use_persistent}, ENVIRONMENT={settings.ENVIRONMENT})"
        )
    
    return None

async def cleanup_auth_stores():
    """Cleanup authentication stores on shutdown."""
    global _redis_store_instance
    
    if _redis_store_instance:
        try:
            # Close Redis connection
            if hasattr(_redis_store_instance, 'redis') and _redis_store_instance.redis:
                await _redis_store_instance.redis.close()
            logger.info("Closed Redis token store connection")
        except Exception as e:
            logger.error(f"Error closing Redis token store: {e}")
        
        _redis_store_instance = None

def get_refresh_token_store():
    """Get the current refresh token store instance."""
    if _redis_store_instance:
        return _redis_store_instance
    
    # Return the default in-memory store
    from backend.src.services.auth import refresh_token_store
    return refresh_token_store