"""
Authentication service with JWT and refresh token support.
Implements enterprise-grade security best practices.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from uuid import uuid4

from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.models.user import User, UserStatus
from backend.src.schemas.auth import TokenPayload

logger = get_logger(__name__)

# Password hashing context with bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Enterprise-grade security
)


class TokenBlacklist:
    """In-memory token blacklist for revoked tokens."""
    
    def __init__(self):
        self._blacklist: Dict[str, datetime] = {}
    
    def add(self, jti: str, exp: datetime) -> None:
        """Add token to blacklist."""
        self._blacklist[jti] = exp
        # Clean expired tokens
        self._clean_expired()
    
    def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        self._clean_expired()
        return jti in self._blacklist
    
    def _clean_expired(self) -> None:
        """Remove expired tokens from blacklist."""
        now = datetime.now(timezone.utc)
        expired = [jti for jti, exp in self._blacklist.items() if exp < now]
        for jti in expired:
            del self._blacklist[jti]


class RefreshTokenStore:
    """Store for managing refresh token families."""
    
    def __init__(self):
        self._families: Dict[str, Dict[str, Any]] = {}
    
    def create_family(self, user_id: int) -> str:
        """Create a new token family."""
        family_id = str(uuid4())
        self._families[family_id] = {
            "user_id": user_id,
            "current_token_id": None,
            "used_tokens": set(),
            "created_at": datetime.now(timezone.utc),
            "last_rotation": datetime.now(timezone.utc)
        }
        return family_id
    
    def add_token(self, family_id: str, token_id: str) -> None:
        """Add token to family."""
        if family_id in self._families:
            family = self._families[family_id]
            if family["current_token_id"]:
                family["used_tokens"].add(family["current_token_id"])
            family["current_token_id"] = token_id
            family["last_rotation"] = datetime.now(timezone.utc)
    
    def validate_token(self, family_id: str, token_id: str) -> bool:
        """Validate token and detect reuse."""
        if family_id not in self._families:
            return False
        
        family = self._families[family_id]
        
        # Check if token was already used (reuse detection)
        if token_id in family["used_tokens"]:
            # Check if this is a recent rotation (within 10 seconds)
            # This handles race conditions where multiple requests use the same token
            if family.get("last_rotation") and \
               (datetime.now(timezone.utc) - family["last_rotation"]).total_seconds() < 10:
                logger.info(
                    "refresh_token_race_condition_detected",
                    family_id=family_id,
                    token_id=token_id,
                    user_id=family["user_id"]
                )
                # Allow the current token instead
                return family["current_token_id"] == token_id
            
            # Token reuse detected - invalidate entire family
            logger.warning(
                "refresh_token_reuse_detected",
                family_id=family_id,
                token_id=token_id,
                user_id=family["user_id"]
            )
            del self._families[family_id]
            return False
        
        # Check if token is current
        return family["current_token_id"] == token_id
    
    def get_user_id(self, family_id: str) -> Optional[int]:
        """Get user ID for token family."""
        family = self._families.get(family_id)
        return family["user_id"] if family else None
    
    def revoke_family(self, family_id: str) -> None:
        """Revoke entire token family."""
        if family_id in self._families:
            del self._families[family_id]
    
    def revoke_user_families(self, user_id: int) -> None:
        """Revoke all token families for a user."""
        families_to_revoke = [
            fid for fid, family in self._families.items()
            if family["user_id"] == user_id
        ]
        for family_id in families_to_revoke:
            del self._families[family_id]


# Global instances
token_blacklist = TokenBlacklist()
refresh_token_store = RefreshTokenStore()


class AuthService:
    """Authentication service with JWT support."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(
        user_id: int,
        email: str,
        roles: list[str],
        jti: Optional[str] = None
    ) -> Tuple[str, datetime]:
        """
        Create JWT access token.
        
        Returns:
            Tuple of (token, expiration_time)
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        jti = jti or str(uuid4())
        
        payload = {
            "sub": str(user_id),
            "email": email,
            "roles": roles,
            "exp": expire,
            "iat": now,
            "jti": jti,
            "type": "access"
        }
        
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return token, expire
    
    @staticmethod
    def create_refresh_token(
        user_id: int,
        family_id: Optional[str] = None
    ) -> Tuple[str, str, datetime]:
        """
        Create JWT refresh token with family tracking.
        
        Returns:
            Tuple of (token, family_id, expiration_time)
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        token_id = str(uuid4())
        
        # Create or use existing family
        if not family_id:
            family_id = refresh_token_store.create_family(user_id)
        
        # Add token to family
        refresh_token_store.add_token(family_id, token_id)
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "jti": token_id,
            "family": family_id,
            "type": "refresh"
        }
        
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return token, family_id, expire
    
    @staticmethod
    def decode_token(token: str) -> TokenPayload:
        """
        Decode and validate JWT token.
        
        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and token_blacklist.is_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            return TokenPayload(**payload)
            
        except JWTError as e:
            logger.error("jwt_decode_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with username/email and password.
        
        Args:
            db: Database session
            username: Username or email
            password: Plain password
            
        Returns:
            User if authenticated, None otherwise
        """
        # Check if username is email
        if "@" in username:
            query = select(User).where(
                and_(
                    User.email == username,
                    User.is_deleted == False
                )
            )
        else:
            query = select(User).where(
                and_(
                    User.username == username,
                    User.is_deleted == False
                )
            )
        
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Check password
        if not AuthService.verify_password(password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
                logger.warning(
                    "account_locked",
                    user_id=user.id,
                    attempts=user.failed_login_attempts
                )
            
            await db.commit()
            return None
        
        # Check if account is locked
        if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
            return None
        
        # Check if account is active
        # TEMPORARY: Allow pending users in development mode for testing
        if settings.DEBUG:
            if user.status not in [UserStatus.active, UserStatus.pending]:
                return None
        else:
            if user.status != UserStatus.active:
                return None
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        
        await db.commit()
        return user
    
    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str
    ) -> Tuple[str, str, datetime, datetime]:
        """
        Refresh access token using refresh token.
        
        Returns:
            Tuple of (access_token, refresh_token, access_exp, refresh_exp)
        """
        # Decode refresh token
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Validate token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Validate token family
        family_id = payload.get("family")
        token_id = payload.get("jti")
        
        if not refresh_token_store.validate_token(family_id, token_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or reused refresh token"
            )
        
        # Get user
        user_id = int(payload.get("sub"))
        query = select(User).where(
            and_(
                User.id == user_id,
                User.is_deleted == False,
                User.status == UserStatus.active
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # Revoke token family if user not found
            refresh_token_store.revoke_family(family_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Get user roles
        roles = [role.name for role in user.roles]
        
        # Create new token pair
        access_token, access_exp = AuthService.create_access_token(
            user_id=user.id,
            email=user.email,
            roles=roles
        )
        
        new_refresh_token, _, refresh_exp = AuthService.create_refresh_token(
            user_id=user.id,
            family_id=family_id
        )
        
        return access_token, new_refresh_token, access_exp, refresh_exp
    
    @staticmethod
    def revoke_token(token: str) -> None:
        """Revoke a token by adding it to blacklist."""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            jti = payload.get("jti")
            exp = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
            
            if jti:
                token_blacklist.add(jti, exp)
                
                # If refresh token, revoke entire family
                if payload.get("type") == "refresh":
                    family_id = payload.get("family")
                    if family_id:
                        refresh_token_store.revoke_family(family_id)
                        
        except JWTError:
            pass  # Invalid token, ignore
    
    @staticmethod
    def revoke_all_user_tokens(user_id: int) -> None:
        """Revoke all tokens for a user."""
        refresh_token_store.revoke_user_families(user_id)
        # Note: Access tokens can't be fully revoked without a persistent store
        logger.info("user_tokens_revoked", user_id=user_id)
    
    @staticmethod
    async def verify_email_token(
        db: AsyncSession,
        token: str
    ) -> Optional[User]:
        """Verify email verification token."""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            if payload.get("type") != "email_verification":
                return None
            
            user_id = int(payload.get("sub"))
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if user and not user.email_verified:
                user.email_verified = True
                user.email_verified_at = datetime.now(timezone.utc)
                if user.status == UserStatus.pending:
                    user.status = UserStatus.active
                await db.commit()
                return user
                
        except JWTError:
            pass
        
        return None
    
    @staticmethod
    def create_email_verification_token(user_id: int, email: str) -> str:
        """Create email verification token."""
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
        
        payload = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "type": "email_verification"
        }
        
        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    @staticmethod
    def create_password_reset_token(user_id: int, email: str) -> str:
        """Create password reset token."""
        expire = datetime.now(timezone.utc) + timedelta(hours=1)
        
        payload = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "type": "password_reset",
            "jti": str(uuid4())
        }
        
        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    @staticmethod
    async def reset_password(
        db: AsyncSession,
        token: str,
        new_password: str
    ) -> Optional[User]:
        """Reset user password with token."""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            if payload.get("type") != "password_reset":
                return None
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and token_blacklist.is_blacklisted(jti):
                return None
            
            user_id = int(payload.get("sub"))
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if user:
                user.password_hash = AuthService.hash_password(new_password)
                # Revoke all user tokens on password reset
                AuthService.revoke_all_user_tokens(user.id)
                # Blacklist the reset token
                if jti:
                    exp = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
                    token_blacklist.add(jti, exp)
                await db.commit()
                return user
                
        except JWTError:
            pass
        
        return None