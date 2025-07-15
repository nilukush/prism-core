"""
Security utilities for authentication and authorization.
Handles JWT tokens, password hashing, and access control.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityError(Exception):
    """Base security exception."""
    pass


class TokenError(SecurityError):
    """Token-related errors."""
    pass


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create JWT access token.
    
    Args:
        subject: Token subject (usually user ID)
        expires_delta: Token expiration time
        additional_claims: Additional JWT claims
        
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.now(timezone.utc),
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    logger.debug("access_token_created", subject=subject)
    return encoded_jwt


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create JWT refresh token.
    
    Args:
        subject: Token subject (usually user ID)
        expires_delta: Token expiration time
        additional_claims: Additional JWT claims
        
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    logger.debug("refresh_token_created", subject=subject)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Token payload
        
    Raises:
        TokenError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning("token_decode_failed", error=str(e))
        raise TokenError("Invalid or expired token") from e


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        Verification result
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password.
    
    Args:
        password: Plain text password
        
    Returns:
        Password hash
    """
    return pwd_context.hash(password)


def generate_password_reset_token(email: str) -> str:
    """
    Generate password reset token.
    
    Args:
        email: User email
        
    Returns:
        Reset token
    """
    delta = timedelta(hours=24)
    return create_access_token(
        subject=email,
        expires_delta=delta,
        additional_claims={"type": "password_reset"}
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token.
    
    Args:
        token: Reset token
        
    Returns:
        Email address if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except TokenError:
        return None


def generate_email_verification_token(email: str) -> str:
    """
    Generate email verification token.
    
    Args:
        email: User email
        
    Returns:
        Verification token
    """
    delta = timedelta(days=7)
    return create_access_token(
        subject=email,
        expires_delta=delta,
        additional_claims={"type": "email_verification"}
    )


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    Verify email verification token.
    
    Args:
        token: Verification token
        
    Returns:
        Email address if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "email_verification":
            return None
        return payload.get("sub")
    except TokenError:
        return None


class PermissionChecker:
    """Permission checking utility."""
    
    def __init__(self, required_permissions: list[str]):
        """
        Initialize permission checker.
        
        Args:
            required_permissions: List of required permission names
        """
        self.required_permissions = required_permissions
    
    def __call__(self, user_permissions: list[str]) -> bool:
        """
        Check if user has required permissions.
        
        Args:
            user_permissions: List of user's permissions
            
        Returns:
            True if user has all required permissions
        """
        return all(
            permission in user_permissions
            for permission in self.required_permissions
        )


# Common permission checkers
can_create_stories = PermissionChecker(["stories.create"])
can_edit_stories = PermissionChecker(["stories.edit"])
can_delete_stories = PermissionChecker(["stories.delete"])
can_create_documents = PermissionChecker(["documents.create"])
can_edit_documents = PermissionChecker(["documents.edit"])
can_delete_documents = PermissionChecker(["documents.delete"])
can_manage_users = PermissionChecker(["users.manage"])
can_manage_organization = PermissionChecker(["organization.manage"])
can_access_analytics = PermissionChecker(["analytics.view"])
can_manage_integrations = PermissionChecker(["integrations.manage"])