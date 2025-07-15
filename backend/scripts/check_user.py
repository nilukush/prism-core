"""
Check user status in database.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.core.database import AsyncSessionLocal
from backend.src.models.user import User
from backend.src.services.auth import AuthService


async def check_user(email: str):
    """Check user status and details."""
    async with AsyncSessionLocal() as session:
        # Query user
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User with email {email} not found in database")
            return
        
        print(f"\nUser Details:")
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Username: {user.username}")
        print(f"Full Name: {user.full_name}")
        print(f"Status: {user.status}")
        print(f"Email Verified: {user.email_verified}")
        print(f"Is Deleted: {user.is_deleted}")
        print(f"Created At: {user.created_at}")
        print(f"Failed Login Attempts: {user.failed_login_attempts}")
        print(f"Locked Until: {user.locked_until}")
        print(f"Last Login: {user.last_login_at}")
        
        # Check if user is active
        print(f"\nIs Active: {user.is_active}")
        print(f"Is Locked: {user.is_locked}")
        
        # Test password
        if len(sys.argv) > 2:
            test_password = sys.argv[2]
            password_valid = AuthService.verify_password(test_password, user.password_hash)
            print(f"\nPassword '{test_password}' is valid: {password_valid}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_user.py <email> [password_to_test]")
        sys.exit(1)
    
    email = sys.argv[1]
    asyncio.run(check_user(email))