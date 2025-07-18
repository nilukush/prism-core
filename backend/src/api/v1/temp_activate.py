"""
Temporary activation endpoint - REMOVE BEFORE PRODUCTION
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.src.api.deps import get_db
from backend.src.models.user import User, UserStatus
from backend.src.core.logging import get_logger
from datetime import datetime, timezone

logger = get_logger(__name__)
router = APIRouter()


@router.post("/activate/{email}")
async def activate_user(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Temporary endpoint to activate user - REMOVE IN PRODUCTION"""
    # Security check - only allow specific email for now
    if email != "nilukush@gmail.com":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log current status
    logger.info(f"User status before: {user.status}, email_verified: {user.email_verified}")
    
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