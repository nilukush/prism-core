"""
API dependencies.
Provides common dependencies for authentication, database sessions, etc.
"""

from typing import Annotated, Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.src.core.database import get_db
from backend.src.models.user import User
from backend.src.services.auth import AuthService
from backend.src.schemas.auth import TokenPayload

# OAuth2 scheme for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# HTTP Bearer for production use
security = HTTPBearer()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get current authenticated user from OAuth2 token.
    
    Args:
        token: Bearer token
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    # Decode token
    token_payload = AuthService.decode_token(token)
    
    # Verify token type
    if token_payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database with roles
    user_id = int(token_payload.sub)
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    return user


async def get_current_user_bearer(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get current authenticated user from Bearer token.
    Alternative to OAuth2 for production APIs.
    
    Args:
        credentials: Bearer token from Authorization header
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    
    # Decode token
    token_payload = AuthService.decode_token(token)
    
    # Verify token type
    if token_payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Get user from database with roles
    user_id = int(token_payload.sub)
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    return current_user


async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Get current user with verified email.
    
    Args:
        current_user: Current active user
        
    Returns:
        Verified user
        
    Raises:
        HTTPException: If email is not verified
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    
    return current_user


class PermissionChecker:
    """
    Permission dependency checker.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(PermissionChecker("admin:read"))])
    """
    
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_verified_user)
    ) -> User:
        """Check if user has required permissions."""
        user_permissions = current_user.get_permissions()
        
        for permission in self.required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
        
        return current_user


class RoleChecker:
    """
    Role dependency checker.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(RoleChecker(["admin", "manager"]))])
    """
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_verified_user)
    ) -> User:
        """Check if user has one of the allowed roles."""
        user_roles = [role.name for role in current_user.roles]
        
        if not any(role in self.allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(self.allowed_roles)}"
            )
        
        return current_user


# Common permission dependencies
require_admin = PermissionChecker(["admin:all"])
require_project_read = PermissionChecker(["project:read"])
require_project_write = PermissionChecker(["project:write"])
require_story_read = PermissionChecker(["story:read"])
require_story_write = PermissionChecker(["story:write"])
require_document_read = PermissionChecker(["document:read"])
require_document_write = PermissionChecker(["document:write"])

# Common role dependencies
require_admin_role = RoleChecker(["admin"])
require_manager_role = RoleChecker(["admin", "manager"])
require_member_role = RoleChecker(["admin", "manager", "member"])


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current authenticated user if token is provided.
    Returns None if no token or invalid token.
    
    Args:
        token: Bearer token (optional)
        db: Database session
        
    Returns:
        Current user or None
    """
    if not token:
        return None
        
    try:
        # Decode token
        token_payload = AuthService.decode_token(token)
        
        # Verify token type
        if token_payload.type != "access":
            return None
        
        # Get user from database with roles
        user_id = int(token_payload.sub)
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user and user.is_active:
            return user
            
    except Exception:
        pass
        
    return None


def require_permissions(user: User, permissions: List[str]) -> None:
    """
    Check if user has required permissions.
    Raises HTTPException if permissions are missing.
    
    Args:
        user: User to check permissions for
        permissions: List of required permissions
        
    Raises:
        HTTPException: If user lacks required permissions
    """
    user_permissions = user.get_permissions()
    
    for permission in permissions:
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )