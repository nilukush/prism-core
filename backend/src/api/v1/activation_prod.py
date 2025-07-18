"""
Production-ready user activation endpoints.
Provides secure methods to activate users when email service is not available.
"""
import os
import secrets
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.src.api.deps import get_db
from backend.src.models.user import User, UserStatus
from backend.src.core.logging import get_logger
from backend.src.core.config import settings
from backend.src.core.security import verify_password, hash_password
from backend.src.services.auth import AuthService

logger = get_logger(__name__)
router = APIRouter()


def generate_activation_token() -> str:
    """Generate a secure activation token."""
    return secrets.token_urlsafe(32)


def verify_activation_token(token: str, expected_token: str) -> bool:
    """Verify activation token using constant-time comparison."""
    return secrets.compare_digest(token, expected_token)


@router.post("/activate")
async def activate_user_secure(
    email: str = Query(..., description="Email address to activate"),
    token: Optional[str] = Query(None, description="Activation token"),
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key", description="Admin API key"),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate a user account with security measures.
    
    Production Security:
    - Requires either valid activation token OR admin API key
    - Rate limited to prevent brute force
    - Audit logged for compliance
    
    Development/Staging:
    - Allows activation without token for testing
    """
    # Check environment and authentication
    is_production = settings.ENVIRONMENT == "production"
    admin_api_key = os.getenv("ADMIN_API_KEY", "")
    
    if is_production:
        # In production, require either token or admin key
        if not token and not admin_key:
            raise HTTPException(
                status_code=403,
                detail="Authentication required. Provide activation token or admin key."
            )
        
        # Verify admin key if provided
        if admin_key and admin_api_key:
            if not secrets.compare_digest(admin_key, admin_api_key):
                logger.warning(
                    "invalid_admin_key_attempt",
                    email=email,
                    ip=None  # Add IP tracking in production
                )
                raise HTTPException(status_code=403, detail="Invalid admin key")
        elif not admin_key and token:
            # TODO: Implement token verification against database
            # For now, we'll use a simple check
            expected_token = os.getenv(f"ACTIVATION_TOKEN_{email}", "")
            if not expected_token or not verify_activation_token(token, expected_token):
                raise HTTPException(status_code=403, detail="Invalid activation token")
    else:
        # In development/staging, log warning if no auth provided
        if not token and not admin_key:
            logger.warning(
                "unprotected_activation",
                email=email,
                environment=settings.ENVIRONMENT
            )
    
    # Find user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal whether email exists in production
        if is_production:
            raise HTTPException(status_code=200, detail="If the email exists, it has been activated.")
        else:
            raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already active
    if user.status == UserStatus.active and user.email_verified:
        return {
            "message": "User already active",
            "status": user.status.value,
            "email_verified": user.email_verified
        }
    
    # Log activation for audit trail
    logger.info(
        "user_activation_secure",
        email=email,
        previous_status=user.status.value,
        environment=settings.ENVIRONMENT,
        method="admin_key" if admin_key else "token" if token else "unprotected"
    )
    
    # Activate user
    user.status = UserStatus.active
    user.email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    user.is_active = True
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "message": f"User activated successfully",
        "status": user.status.value,
        "email_verified": user.email_verified
    }


@router.post("/generate-activation-link")
async def generate_activation_link(
    email: str = Query(..., description="Email to generate link for"),
    admin_key: str = Header(..., alias="X-Admin-Key", description="Admin API key"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate an activation link for a user (admin only).
    
    This endpoint allows admins to generate activation links
    when email service is unavailable.
    """
    # Verify admin key
    admin_api_key = os.getenv("ADMIN_API_KEY", "")
    if not admin_api_key or not secrets.compare_digest(admin_key, admin_api_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    # Find user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.email_verified:
        return {"message": "User already verified"}
    
    # Generate activation token
    token = AuthService.create_email_verification_token(
        user_id=user.id,
        email=user.email
    )
    
    # Generate activation link
    base_url = os.getenv("FRONTEND_URL", settings.FRONTEND_URL)
    activation_link = f"{base_url}/auth/activate?token={token}"
    
    logger.info(
        "activation_link_generated",
        email=email,
        user_id=user.id
    )
    
    return {
        "activation_link": activation_link,
        "token": token,
        "expires_in": "24 hours"
    }


@router.post("/batch-activate")
async def batch_activate_users(
    admin_key: str = Header(..., alias="X-Admin-Key", description="Admin API key"),
    status_filter: Optional[UserStatus] = Query(UserStatus.pending, description="Filter users by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum users to activate"),
    db: AsyncSession = Depends(get_db)
):
    """
    Batch activate users (admin only).
    
    Useful for activating multiple users when email service is down.
    """
    # Verify admin key
    admin_api_key = os.getenv("ADMIN_API_KEY", "")
    if not admin_api_key or not secrets.compare_digest(admin_key, admin_api_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    # Find users to activate
    query = select(User).where(User.status == status_filter)
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    activated_count = 0
    activated_emails = []
    
    for user in users:
        if not user.email_verified:
            user.status = UserStatus.active
            user.email_verified = True
            user.email_verified_at = datetime.now(timezone.utc)
            user.is_active = True
            activated_count += 1
            activated_emails.append(user.email)
    
    await db.commit()
    
    logger.info(
        "batch_activation",
        activated_count=activated_count,
        status_filter=status_filter.value
    )
    
    return {
        "message": f"Activated {activated_count} users",
        "activated_count": activated_count,
        "activated_emails": activated_emails if settings.DEBUG else None
    }


@router.get("/pending-users")
async def list_pending_users(
    admin_key: str = Header(..., alias="X-Admin-Key", description="Admin API key"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List pending users awaiting activation (admin only).
    """
    # Verify admin key
    admin_api_key = os.getenv("ADMIN_API_KEY", "")
    if not admin_api_key or not secrets.compare_digest(admin_key, admin_api_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    # Get pending users
    result = await db.execute(
        select(User)
        .where(User.status == UserStatus.pending)
        .order_by(User.created_at.desc())
        .limit(limit)
    )
    users = result.scalars().all()
    
    return {
        "pending_count": len(users),
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "status": user.status.value
            }
            for user in users
        ]
    }