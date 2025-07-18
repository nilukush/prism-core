"""
Simple activation endpoint that works in production.
Minimal dependencies to avoid import errors.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.src.api.deps import get_db
from backend.src.models.user import User, UserStatus

router = APIRouter()


@router.post("/simple/{email}")
async def activate_user_simple(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Simple activation endpoint that always works.
    For production use with email verification issues.
    """
    try:
        # First check if user exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {"error": "User not found", "email": email}
        
        # Update user
        user.status = UserStatus.active
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        user.is_active = True
        
        await db.commit()
        
        return {
            "message": f"User {email} activated successfully",
            "status": "active",
            "email_verified": True
        }
        
    except Exception as e:
        await db.rollback()
        return {
            "error": "Activation failed",
            "details": str(e),
            "email": email
        }