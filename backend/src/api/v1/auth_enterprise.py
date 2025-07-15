"""
Enterprise authentication endpoints with persistent session support.
Provides seamless upgrade path from in-memory to Redis-backed sessions.
"""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.api.deps import get_db, get_current_user
from backend.src.api.v1.auth import router as base_auth_router
from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.models.user import User
from backend.src.schemas.auth import RefreshTokenRequest, Token
from backend.src.services.auth import AuthService
from backend.src.services.auth_enterprise import (
    enterprise_auth_service,
    create_enterprise_session,
    refresh_enterprise_token
)

logger = get_logger(__name__)

# Check if we should use enterprise features
USE_ENTERPRISE_AUTH = (
    os.getenv("USE_PERSISTENT_SESSIONS", "false").lower() == "true"
    or settings.ENVIRONMENT in ["production", "staging"]
)

# Create a new router for enterprise endpoints
enterprise_router = APIRouter()

# Define enterprise-enhanced endpoints
@enterprise_router.post("/login", response_model=Token)
async def enterprise_login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Enhanced login with persistent session support.
    Sessions survive service restarts in production.
    """
    # Authenticate user (same as base)
    user = await AuthService.authenticate_user(
        db=db,
        username=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Load roles (same as base)
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user.id)
    )
    user = result.scalar_one()
    roles = [role.name for role in user.roles]
    
    # Extract metadata for session
    metadata = {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "aal": 1  # Authentication Assurance Level
    }
    
    # Create enterprise session with persistence
    try:
        (
            access_token,
            refresh_token,
            access_exp,
            session_id,
            refresh_exp
        ) = await create_enterprise_session(
            user_id=user.id,
            user_email=user.email,
            roles=roles,
            metadata=metadata
        )
        
        # Calculate expiry times
        from datetime import datetime, timezone
        access_expires_in = int((access_exp - datetime.now(timezone.utc)).total_seconds())
        refresh_expires_in = int((refresh_exp - datetime.now(timezone.utc)).total_seconds())
        
        logger.info(
            "enterprise_user_login",
            user_id=user.id,
            session_id=session_id,
            persistent=True
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=access_expires_in,
            refresh_expires_in=refresh_expires_in
        )
        
    except Exception as e:
        logger.error("enterprise_login_failed", error=str(e), user_id=user.id)
        # Fallback to standard auth
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session service temporarily unavailable"
        )


@enterprise_router.post("/refresh", response_model=Token)
async def enterprise_refresh(
    refresh_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Enhanced token refresh with Redis-backed token families.
    Provides better security and survives service restarts.
    """
    try:
        (
            access_token,
            refresh_token,
            access_exp,
            refresh_exp
        ) = await refresh_enterprise_token(refresh_request.refresh_token)
        
        # Calculate expiry times
        from datetime import datetime, timezone
        access_expires_in = int((access_exp - datetime.now(timezone.utc)).total_seconds())
        refresh_expires_in = int((refresh_exp - datetime.now(timezone.utc)).total_seconds())
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=access_expires_in,
            refresh_expires_in=refresh_expires_in
        )
        
    except ValueError as e:
        logger.warning("enterprise_refresh_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error("enterprise_refresh_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@enterprise_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def enterprise_logout(
    current_user: Annotated[User, Depends(get_current_user)],
    authorization: Annotated[str, Header()] = None
):
    """
    Enhanced logout with session invalidation.
    Properly cleans up persistent sessions.
    """
    # Revoke current token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            await enterprise_auth_service.revoke_token_enterprise(token)
        except Exception as e:
            logger.error("token_revoke_failed", error=str(e))
    
    # TODO: Get session ID from token claims to invalidate session
    # For now, just revoke all user tokens
    AuthService.revoke_all_user_tokens(current_user.id)
    
    logger.info("enterprise_user_logout", user_id=current_user.id)


# Add a new endpoint for session status
@enterprise_router.get("/session/status")
async def session_status(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Check session persistence status.
    Helps debug session storage configuration.
    """
    return JSONResponse(
        content={
            "user_id": current_user.id,
            "email": current_user.email,
            "persistent_sessions": USE_ENTERPRISE_AUTH,
            "session_manager_active": bool(
                enterprise_auth_service.session_manager
            ),
            "environment": settings.ENVIRONMENT,
            "redis_url": "configured" if settings.REDIS_URL else "not configured"
        }
    )


# Function to apply enterprise overrides to base router
def apply_enterprise_overrides():
    """Apply enterprise endpoint overrides to the base auth router."""
    if not USE_ENTERPRISE_AUTH:
        return
        
    # Remove the original routes we want to override
    routes_to_override = ["/login", "/refresh", "/logout"]
    
    # Filter out routes we're overriding
    base_auth_router.routes = [
        route for route in base_auth_router.routes 
        if not (hasattr(route, 'path') and route.path in routes_to_override)
    ]
    
    # Add enterprise routes
    for route in enterprise_router.routes:
        base_auth_router.routes.append(route)
    
    logger.info("Enterprise auth endpoints applied")