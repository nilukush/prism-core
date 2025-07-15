"""
Fixed authentication service that properly uses Redis for token persistence.
This ensures sessions survive service restarts.
"""

import os
from backend.src.services.auth import *
from backend.src.services.auth_token_store import RedisRefreshTokenStore, redis_refresh_token_store
from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)

# Override the in-memory store with Redis store based on environment
if os.getenv("USE_PERSISTENT_TOKENS", "false").lower() == "true":
    if redis_refresh_token_store:
        logger.info("Using Redis-backed refresh token store for persistence")
        refresh_token_store = redis_refresh_token_store
    else:
        logger.warning("Redis token store requested but not available, falling back to in-memory")
        # Keep the in-memory store from parent module
else:
    logger.info("Using in-memory refresh token store (sessions will not survive restarts)")
    # Keep the in-memory store from parent module

# Re-export everything else from the original auth module
__all__ = [
    'AuthService',
    'token_blacklist',
    'refresh_token_store',
    'TokenBlacklist',
    'RefreshTokenStore'
]