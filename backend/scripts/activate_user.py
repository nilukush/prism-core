#!/usr/bin/env python3
"""
Quick script to activate a user account for development testing.
This bypasses email verification.

Usage:
    python scripts/activate_user.py nilukush@gmail.com
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import async_session_maker
from src.models.user import User, UserStatus
from src.core.logging import get_logger

logger = get_logger(__name__)


async def activate_user(email: str) -> None:
    """Activate a user account by email."""
    async with async_session_maker() as db:
        # Find user
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email '{email}' not found")
            return
        
        # Check current status
        print(f"Current user status: {user.status}")
        
        # Activate user
        user.status = UserStatus.active
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        
        await db.commit()
        print(f"✅ User '{email}' has been activated!")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Status: {user.status}")
        print(f"   Email verified: {user.email_verified}")


async def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/activate_user.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    await activate_user(email)


if __name__ == "__main__":
    asyncio.run(main())