"""
Enterprise-grade session management with Redis persistence.
Implements OWASP and NIST standards for secure session handling.
"""

import asyncio
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple
from uuid import uuid4
from enum import Enum

from redis import asyncio as aioredis
from redis.exceptions import RedisError

from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.core.session_config import SessionConfig

logger = get_logger(__name__)


class SessionStatus(str, Enum):
    """Session status states."""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    SUSPICIOUS = "suspicious"


class TokenFamilyStatus(str, Enum):
    """Token family status states."""
    VALID = "valid"
    BREACHED = "breached"
    EXPIRED = "expired"


class EnterpriseSessionManager:
    """
    Enterprise-grade session manager with Redis persistence.
    
    Features:
    - Persistent session storage across service restarts
    - Token family tracking with breach detection
    - Graceful shutdown with session preservation
    - Distributed lock support for multi-instance deployments
    - Audit trail for compliance
    - Automatic cleanup of expired sessions
    """
    
    def __init__(self, redis_url: Optional[str] = None, config: Optional[dict] = None):
        self.redis_url = redis_url or str(settings.REDIS_URL)
        self.redis: Optional[aioredis.Redis] = None
        
        # Load configuration
        self.config = config or SessionConfig.get_config_dict()
        
        # Prefixes for different data types
        self._prefix_session = self.config.get('prefix_session', 'session:')
        self._prefix_token_family = self.config.get('prefix_token_family', 'token:family:')
        self._prefix_token_blacklist = self.config.get('prefix_blacklist', 'token:blacklist:')
        self._prefix_audit = self.config.get('prefix_audit', 'audit:session:')
        self._prefix_lock = self.config.get('prefix_lock', 'lock:session:')
        
        # Configuration
        self._session_ttl = self.config.get('session_ttl', 86400 * 7)  # 7 days
        self._token_family_ttl = self.config.get('token_family_ttl', 86400 * 30)  # 30 days
        self._blacklist_ttl = self.config.get('blacklist_ttl', 86400 * 7)  # 7 days
        self._lock_ttl = self.config.get('lock_ttl', 30)  # 30 seconds for distributed locks
        
        # NIST compliance: 256-bit session IDs
        self._session_id_bytes = self.config.get('session_id_bytes', 32)  # 256 bits
        
        # Additional configuration
        self._redis_retry_max = self.config.get('redis_retry_max', 5)
        self._redis_retry_delay = self.config.get('redis_retry_delay', 1)
        self._redis_retry_backoff = self.config.get('redis_retry_backoff', 2.0)
        self._token_reuse_window = self.config.get('token_reuse_window', 10)
        self._token_family_max_history = self.config.get('token_family_max_history', 20)
        self._cleanup_interval = self.config.get('cleanup_interval', 3600)
        self._audit_retention_days = self.config.get('audit_retention_days', 90)
        self._audit_enabled = self.config.get('audit_enabled', True)
        
    async def initialize(self):
        """Initialize Redis connection with retry logic."""
        max_retries = self._redis_retry_max
        retry_delay = self._redis_retry_delay
        
        for attempt in range(max_retries):
            try:
                # Create Redis connection without platform-specific keepalive options
                # These options can cause "Invalid argument" errors on some systems
                self.redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_keepalive=True
                )
                
                # Test connection
                await self.redis.ping()
                
                logger.info("Enterprise session manager initialized with Redis persistence")
                
                # Start background cleanup task
                asyncio.create_task(self._cleanup_expired_sessions())
                
                return
                
            except Exception as e:
                logger.error(f"Failed to initialize Redis (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= self._redis_retry_backoff
                else:
                    raise
    
    async def create_session(
        self,
        user_id: int,
        user_email: str,
        roles: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Create a new session with OWASP-compliant session ID.
        
        Returns:
            Tuple of (session_id, session_data)
        """
        # Generate cryptographically secure session ID
        session_id = secrets.token_urlsafe(self._session_id_bytes)
        
        session_data = {
            "id": session_id,
            "user_id": user_id,
            "user_email": user_email,
            "roles": roles,
            "status": SessionStatus.ACTIVE,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "ip_address": metadata.get("ip_address") if metadata else None,
            "user_agent": metadata.get("user_agent") if metadata else None,
            "aal": metadata.get("aal", 1) if metadata else 1,  # Authentication Assurance Level
            "binding_secret": secrets.token_urlsafe(
                self.config.get('session_binding_secret_bytes', 32)
            ) if self.config.get('session_binding_enabled', True) else None,
            "refresh_count": 0
        }
        
        # Store in Redis with TTL
        key = f"{self._prefix_session}{session_id}"
        await self.redis.setex(
            key,
            self._session_ttl,
            json.dumps(session_data)
        )
        
        # Create audit entry
        await self._audit_session_event(
            session_id,
            "session_created",
            {"user_id": user_id, "ip": session_data.get("ip_address")}
        )
        
        logger.info(
            "session_created",
            session_id=session_id,
            user_id=user_id,
            user_email=user_email
        )
        
        return session_id, session_data
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        key = f"{self._prefix_session}{session_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        session = json.loads(data)
        
        # Update last activity
        session["last_activity"] = datetime.now(timezone.utc).isoformat()
        await self.redis.setex(key, self._session_ttl, json.dumps(session))
        
        return session
    
    async def invalidate_session(self, session_id: str, reason: str = "logout"):
        """Invalidate a session."""
        key = f"{self._prefix_session}{session_id}"
        data = await self.redis.get(key)
        
        if data:
            session = json.loads(data)
            session["status"] = SessionStatus.INVALIDATED
            session["invalidated_at"] = datetime.now(timezone.utc).isoformat()
            session["invalidation_reason"] = reason
            
            # Keep for audit trail but with shorter TTL
            await self.redis.setex(key, 3600, json.dumps(session))  # 1 hour
            
            # Audit the invalidation
            await self._audit_session_event(
                session_id,
                "session_invalidated",
                {"reason": reason, "user_id": session["user_id"]}
            )
            
            logger.info(
                "session_invalidated",
                session_id=session_id,
                reason=reason,
                user_id=session["user_id"]
            )
    
    # Token Family Management
    
    async def create_token_family(self, user_id: int, session_id: str) -> str:
        """Create a new token family for refresh token rotation."""
        family_id = str(uuid4())
        
        family_data = {
            "family_id": family_id,
            "user_id": user_id,
            "session_id": session_id,
            "generation": 0,
            "current_token_id": None,
            "used_tokens": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_rotation": datetime.now(timezone.utc).isoformat(),
            "status": TokenFamilyStatus.VALID
        }
        
        key = f"{self._prefix_token_family}{family_id}"
        await self.redis.setex(
            key,
            self._token_family_ttl,
            json.dumps(family_data)
        )
        
        logger.info(
            "token_family_created",
            family_id=family_id,
            user_id=user_id,
            session_id=session_id
        )
        
        return family_id
    
    async def rotate_refresh_token(
        self,
        family_id: str,
        old_token_id: str,
        new_token_id: str
    ) -> bool:
        """
        Rotate refresh token with breach detection.
        
        Implements OAuth 2.0 Security BCP for refresh token rotation.
        """
        key = f"{self._prefix_token_family}{family_id}"
        
        # Use distributed lock to prevent race conditions
        lock_key = f"{self._prefix_lock}{family_id}"
        lock_id = str(uuid4())
        
        # Try to acquire lock
        if not await self._acquire_lock(lock_key, lock_id, self._lock_ttl):
            logger.warning(
                "token_rotation_lock_failed",
                family_id=family_id,
                old_token_id=old_token_id
            )
            return False
        
        try:
            data = await self.redis.get(key)
            if not data:
                return False
            
            family = json.loads(data)
            
            # Check if token was already used (breach detection)
            if old_token_id in family["used_tokens"]:
                # Check for race condition (within 10 seconds)
                last_rotation = datetime.fromisoformat(family["last_rotation"])
                if (datetime.now(timezone.utc) - last_rotation).total_seconds() < self._token_reuse_window:
                    logger.info(
                        "token_rotation_race_condition",
                        family_id=family_id,
                        old_token_id=old_token_id
                    )
                    # Allow if it's the current token
                    return family["current_token_id"] == old_token_id
                
                # Breach detected - invalidate entire family
                family["status"] = TokenFamilyStatus.BREACHED
                await self.redis.setex(key, 3600, json.dumps(family))  # Keep for audit
                
                # Invalidate associated session
                await self.invalidate_session(family["session_id"], "token_reuse_detected")
                
                # Audit the breach
                await self._audit_session_event(
                    family["session_id"],
                    "token_breach_detected",
                    {
                        "family_id": family_id,
                        "reused_token": old_token_id,
                        "user_id": family["user_id"]
                    }
                )
                
                logger.error(
                    "token_breach_detected",
                    family_id=family_id,
                    old_token_id=old_token_id,
                    user_id=family["user_id"]
                )
                
                return False
            
            # Validate current token
            if family["current_token_id"] != old_token_id:
                return False
            
            # Rotate token
            if family["current_token_id"]:
                family["used_tokens"].append(family["current_token_id"])
                # Keep only last N used tokens
                family["used_tokens"] = family["used_tokens"][-self._token_family_max_history:]
            
            family["current_token_id"] = new_token_id
            family["generation"] += 1
            family["last_rotation"] = datetime.now(timezone.utc).isoformat()
            
            # Update in Redis
            await self.redis.setex(
                key,
                self._token_family_ttl,
                json.dumps(family)
            )
            
            logger.info(
                "token_rotated",
                family_id=family_id,
                generation=family["generation"],
                user_id=family["user_id"]
            )
            
            return True
            
        finally:
            # Always release lock
            await self._release_lock(lock_key, lock_id)
    
    async def validate_refresh_token(
        self,
        family_id: str,
        token_id: str
    ) -> Optional[Dict[str, Any]]:
        """Validate refresh token and return family data."""
        key = f"{self._prefix_token_family}{family_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        family = json.loads(data)
        
        # Check family status
        if family["status"] != TokenFamilyStatus.VALID:
            return None
        
        # Check if token is current
        if family["current_token_id"] != token_id:
            # Check if it's a used token (potential breach)
            if token_id in family["used_tokens"]:
                # Mark as breached
                family["status"] = TokenFamilyStatus.BREACHED
                await self.redis.setex(key, 3600, json.dumps(family))
                
                # Invalidate session
                await self.invalidate_session(family["session_id"], "token_reuse_detected")
                
                logger.error(
                    "token_reuse_attempt",
                    family_id=family_id,
                    token_id=token_id,
                    user_id=family["user_id"]
                )
            
            return None
        
        return family
    
    # Token Blacklist
    
    async def blacklist_token(self, jti: str, exp: datetime):
        """Add token to blacklist."""
        key = f"{self._prefix_token_blacklist}{jti}"
        ttl = int((exp - datetime.now(timezone.utc)).total_seconds())
        
        if ttl > 0:
            await self.redis.setex(key, ttl, "1")
            logger.info("token_blacklisted", jti=jti)
    
    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        key = f"{self._prefix_token_blacklist}{jti}"
        return await self.redis.exists(key) > 0
    
    # Graceful Shutdown
    
    async def prepare_shutdown(self):
        """Prepare for graceful shutdown."""
        logger.info("Preparing session manager for shutdown")
        
        # Force Redis to save current state
        if self.redis:
            try:
                await self.redis.bgsave()
                logger.info("Redis background save initiated")
            except Exception as e:
                logger.error(f"Failed to initiate Redis save: {e}")
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Session manager closed")
    
    # Helper Methods
    
    async def _acquire_lock(self, key: str, lock_id: str, ttl: int) -> bool:
        """Acquire distributed lock."""
        return await self.redis.set(key, lock_id, nx=True, ex=ttl) is not None
    
    async def _release_lock(self, key: str, lock_id: str):
        """Release distributed lock if we own it."""
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        await self.redis.eval(lua_script, 1, key, lock_id)
    
    async def _audit_session_event(
        self,
        session_id: str,
        event_type: str,
        details: Dict[str, Any]
    ):
        """Create audit trail entry."""
        audit_entry = {
            "session_id": session_id,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details
        }
        
        if not self._audit_enabled:
            return
            
        # Store with daily key for easy retrieval
        date_key = datetime.now(timezone.utc).strftime("%Y%m%d")
        key = f"{self._prefix_audit}{date_key}"
        
        # Add to sorted set with timestamp as score
        score = datetime.now(timezone.utc).timestamp()
        await self.redis.zadd(key, {json.dumps(audit_entry): score})
        
        # Set TTL for audit entries
        await self.redis.expire(key, 86400 * self._audit_retention_days)
    
    async def _cleanup_expired_sessions(self):
        """Background task to cleanup expired sessions."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)  # Run periodically
                
                # This is handled by Redis TTL, but we can add additional cleanup
                logger.info("Session cleanup task completed")
                
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")


# Global instance for easy access
enterprise_session_manager: Optional[EnterpriseSessionManager] = None


async def get_session_manager() -> EnterpriseSessionManager:
    """Get or create the global session manager instance."""
    global enterprise_session_manager
    
    if not enterprise_session_manager:
        enterprise_session_manager = EnterpriseSessionManager()
        await enterprise_session_manager.initialize()
    
    return enterprise_session_manager