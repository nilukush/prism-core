"""
Simple activation endpoint that works in production.
Minimal dependencies to avoid import errors.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.src.api.deps import get_db
from backend.src.models.user import User

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
        # Update user directly
        result = await db.execute(
            update(User)
            .where(User.email == email)
            .values(
                status="active",
                email_verified=True,
                email_verified_at=datetime.now(timezone.utc),
                is_active=True
            )
            .returning(User.id, User.email)
        )
        
        updated = result.first()
        if not updated:
            return {"error": "User not found", "email": email}
        
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