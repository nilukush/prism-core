"""
User activation endpoints for development and testing.
Provides a way to activate users when email verification is not configured.
"""
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.src.api.deps import get_db
from backend.src.models.user import User, UserStatus
from backend.src.core.logging import get_logger
from backend.src.core.config import settings

logger = get_logger(__name__)
router = APIRouter()


@router.post("/activate/{email}")
async def activate_user(
    email: str,
    token: Optional[str] = Query(None, description="Activation token or admin key"),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate a user account.
    
    In development: No token required
    In production: Requires activation token or admin key
    """
    # In production, require a token
    if settings.ENVIRONMENT == "production":
        admin_key = os.getenv("ADMIN_ACTIVATION_KEY", "")
        if not token or (token != admin_key and len(admin_key) > 0):
            raise HTTPException(
                status_code=403, 
                detail="Activation token required in production"
            )
    
    # Find user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already active
    if user.status == UserStatus.active and user.email_verified:
        return {
            "message": "User already active",
            "status": user.status.value,
            "email_verified": user.email_verified
        }
    
    # Log activation
    logger.info(
        "user_activation", 
        email=email,
        previous_status=user.status.value,
        environment=settings.ENVIRONMENT
    )
    
    # Activate user
    user.status = UserStatus.active
    user.email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    user.is_active = True
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "message": f"User {email} activated successfully",
        "status": user.status.value,
        "email_verified": user.email_verified
    }


@router.get("/status/{email}")
async def check_user_status(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Check user activation status"""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": user.email,
        "status": user.status.value,
        "email_verified": user.email_verified,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.post("/activate-all-pending")
async def activate_all_pending_users(
    admin_key: Optional[str] = Query(None, description="Admin key required"),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate all pending users - useful for development/testing
    """
    # Require admin key even in development for this bulk operation
    expected_key = os.getenv("ADMIN_ACTIVATION_KEY", "dev-activate-key")
    if admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    # Find all pending users
    result = await db.execute(
        select(User).where(User.status == UserStatus.pending)
    )
    pending_users = result.scalars().all()
    
    activated_count = 0
    for user in pending_users:
        user.status = UserStatus.active
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        user.is_active = True
        activated_count += 1
    
    await db.commit()
    
    return {
        "message": f"Activated {activated_count} users",
        "activated_count": activated_count
    }