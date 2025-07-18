"""
Debug endpoints for development only.
These should be disabled in production.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.src.api.deps import get_db
from backend.src.core.config import settings
from backend.src.models.user import User, UserStatus
from backend.src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/user-status/{email}")
async def check_user_status(
    email: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Debug endpoint to check user status.
    Only available in DEBUG mode.
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available"
        )
    
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return {"error": "User not found"}
    
    return {
        "email": user.email,
        "username": user.username,
        "status": user.status,
        "email_verified": user.email_verified,
        "is_active": user.is_active,
        "is_deleted": user.is_deleted,
        "failed_login_attempts": user.failed_login_attempts,
        "locked_until": user.locked_until.isoformat() if user.locked_until else None,
        "created_at": user.created_at.isoformat(),
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
    }


@router.post("/activate-user/{email}")
async def activate_user_debug(
    email: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Debug endpoint to activate a user.
    Only available in DEBUG mode.
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available"
        )
    
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Activate user
    user.status = UserStatus.active
    user.email_verified = True
    user.is_active = True
    
    await db.commit()
    
    logger.info("debug_user_activated", user_id=user.id, email=email)
    
    return {
        "message": "User activated successfully",
        "email": user.email,
        "status": user.status,
        "email_verified": user.email_verified
    }