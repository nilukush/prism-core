"""
Enterprise authentication service with persistent session management.
Integrates Redis-backed session storage for production resilience.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

from backend.src.services.auth import AuthService as BaseAuthService
from backend.src.services.session_manager import (
    get_session_manager,
    EnterpriseSessionManager
)
from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class EnterpriseAuthService(BaseAuthService):
    """
    Enhanced authentication service with enterprise features:
    - Persistent session storage
    - Zero-downtime deployments
    - Distributed token management
    - Comprehensive audit trail
    """
    
    def __init__(self):
        self.session_manager: Optional[EnterpriseSessionManager] = None
        self._use_persistent_sessions = (
            os.getenv("USE_PERSISTENT_SESSIONS", "false").lower() == "true"
            or settings.ENVIRONMENT in ["production", "staging"]
        )
    
    async def initialize(self):
        """Initialize enterprise session manager."""
        if self._use_persistent_sessions:
            try:
                self.session_manager = await get_session_manager()
                logger.info("Enterprise authentication initialized with persistent sessions")
            except Exception as e:
                logger.error(f"Failed to initialize session manager: {e}")
                logger.warning("Falling back to in-memory session storage")
                self._use_persistent_sessions = False
    
    async def create_session(
        self,
        user_id: int,
        user_email: str,
        roles: list[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, datetime, str, datetime]:
        """
        Create session and tokens with enterprise persistence.
        
        Returns:
            Tuple of (access_token, refresh_token, access_exp, session_id, refresh_exp)
        """
        # Create persistent session if enabled
        session_id = None
        if self._use_persistent_sessions and self.session_manager:
            session_id, session_data = await self.session_manager.create_session(
                user_id=user_id,
                user_email=user_email,
                roles=roles,
                metadata=metadata
            )
        
        # Create access token
        access_token, access_exp = self.create_access_token(
            user_id=user_id,
            email=user_email,
            roles=roles
        )
        
        # Create refresh token with family tracking
        if self._use_persistent_sessions and self.session_manager and session_id:
            # Create token family in Redis
            family_id = await self.session_manager.create_token_family(
                user_id=user_id,
                session_id=session_id
            )
            
            # Create refresh token with family ID
            refresh_token, _, refresh_exp = self.create_refresh_token(
                user_id=user_id,
                family_id=family_id
            )
            
            # Store initial token in family
            token_payload = self.decode_token(refresh_token)
            await self.session_manager.rotate_refresh_token(
                family_id=family_id,
                old_token_id=None,  # First token
                new_token_id=token_payload.jti
            )
        else:
            # Fallback to in-memory token management
            refresh_token, family_id, refresh_exp = self.create_refresh_token(
                user_id=user_id
            )
        
        logger.info(
            "enterprise_session_created",
            user_id=user_id,
            session_id=session_id,
            persistent=self._use_persistent_sessions
        )
        
        return access_token, refresh_token, access_exp, session_id or "", refresh_exp
    
    async def refresh_access_token_enterprise(
        self,
        refresh_token: str
    ) -> Tuple[str, str, datetime, datetime]:
        """
        Enhanced refresh token with Redis persistence.
        
        Returns:
            Tuple of (access_token, refresh_token, access_exp, refresh_exp)
        """
        # Decode the refresh token
        try:
            payload = self.decode_token(refresh_token)
        except Exception:
            raise ValueError("Invalid refresh token")
        
        # Check if using persistent sessions
        if self._use_persistent_sessions and self.session_manager:
            # Convert payload to dict to access custom claims
            payload_dict = payload.model_dump() if hasattr(payload, 'model_dump') else payload.dict()
            family_id = payload_dict.get("family")
            token_id = payload.jti
            
            # Validate token with Redis
            family_data = await self.session_manager.validate_refresh_token(
                family_id=family_id,
                token_id=token_id
            )
            
            if not family_data:
                raise ValueError("Invalid or expired refresh token")
            
            # Get session data
            session_data = await self.session_manager.get_session(
                family_data["session_id"]
            )
            
            if not session_data:
                raise ValueError("Session not found")
            
            # Create new tokens
            access_token, access_exp = self.create_access_token(
                user_id=family_data["user_id"],
                email=session_data["user_email"],
                roles=session_data["roles"]
            )
            
            new_refresh_token, _, refresh_exp = self.create_refresh_token(
                user_id=family_data["user_id"],
                family_id=family_id
            )
            
            # Rotate refresh token in Redis
            new_payload = self.decode_token(new_refresh_token)
            await self.session_manager.rotate_refresh_token(
                family_id=family_id,
                old_token_id=token_id,
                new_token_id=new_payload.jti
            )
            
            return access_token, new_refresh_token, access_exp, refresh_exp
        
        else:
            # Fallback to base implementation
            from backend.src.core.database import get_db_sync
            from backend.src.services.auth import AuthService
            
            # This is a simplified version - in production, use async properly
            raise NotImplementedError(
                "In-memory refresh not supported in enterprise service. "
                "Enable USE_PERSISTENT_SESSIONS=true"
            )
    
    async def invalidate_session(
        self,
        session_id: str,
        reason: str = "logout"
    ):
        """Invalidate a session and all associated tokens."""
        if self._use_persistent_sessions and self.session_manager:
            await self.session_manager.invalidate_session(session_id, reason)
    
    async def revoke_token_enterprise(self, token: str):
        """Revoke token with Redis blacklist."""
        try:
            payload = self.decode_token(token)
            
            # Add to Redis blacklist if using persistent sessions
            if self._use_persistent_sessions and self.session_manager:
                exp = datetime.fromtimestamp(payload.exp, tz=timezone.utc)
                await self.session_manager.blacklist_token(payload.jti, exp)
            
            # Also use in-memory blacklist for immediate effect
            self.revoke_token(token)
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
    
    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted in Redis."""
        if self._use_persistent_sessions and self.session_manager:
            return await self.session_manager.is_token_blacklisted(jti)
        
        # Fallback to in-memory check
        from backend.src.services.auth import token_blacklist
        return token_blacklist.is_blacklisted(jti)
    
    async def prepare_shutdown(self):
        """Prepare for graceful shutdown."""
        if self._use_persistent_sessions and self.session_manager:
            await self.session_manager.prepare_shutdown()
    
    async def close(self):
        """Close connections."""
        if self._use_persistent_sessions and self.session_manager:
            await self.session_manager.close()


# Create global instance
enterprise_auth_service = EnterpriseAuthService()


# Helper functions for backward compatibility
async def create_enterprise_session(
    user_id: int,
    user_email: str,
    roles: list[str],
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, datetime, str, datetime]:
    """Create session using enterprise service."""
    if not enterprise_auth_service.session_manager:
        await enterprise_auth_service.initialize()
    
    return await enterprise_auth_service.create_session(
        user_id, user_email, roles, metadata
    )


async def refresh_enterprise_token(
    refresh_token: str
) -> Tuple[str, str, datetime, datetime]:
    """Refresh token using enterprise service."""
    if not enterprise_auth_service.session_manager:
        await enterprise_auth_service.initialize()
    
    return await enterprise_auth_service.refresh_access_token_enterprise(
        refresh_token
    )