#!/usr/bin/env python3
"""
Script to activate user accounts.
Usage: python scripts/activate_user.py --email user@example.com
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from backend.src.core.database import get_async_engine, AsyncSessionLocal
from backend.src.models.user import User, UserStatus
from datetime import datetime, timezone


async def activate_user(email: str):
    """Activate a user by email"""
    async with AsyncSessionLocal() as db:
        # Find user
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email '{email}' not found")
            return False
        
        # Check current status
        print(f"Current status: {user.status.value}")
        print(f"Email verified: {user.email_verified}")
        print(f"Is active: {user.is_active}")
        
        if user.status == UserStatus.active and user.email_verified:
            print(f"✅ User '{email}' is already activated")
            return True
        
        # Activate user
        user.status = UserStatus.active
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        user.is_active = True
        
        await db.commit()
        
        print(f"✅ User '{email}' activated successfully!")
        print(f"New status: {user.status.value}")
        print(f"Email verified: {user.email_verified}")
        
        return True


async def list_pending_users():
    """List all pending users"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.status == UserStatus.pending)
        )
        users = result.scalars().all()
        
        if not users:
            print("No pending users found")
            return
        
        print(f"\nFound {len(users)} pending users:")
        print("-" * 50)
        for user in users:
            print(f"Email: {user.email}")
            print(f"  Username: {user.username or 'N/A'}")
            print(f"  Created: {user.created_at}")
            print(f"  Email verified: {user.email_verified}")
            print("-" * 50)


async def activate_all_pending():
    """Activate all pending users"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.status == UserStatus.pending)
        )
        users = result.scalars().all()
        
        if not users:
            print("No pending users to activate")
            return
        
        print(f"Found {len(users)} pending users to activate")
        
        for user in users:
            user.status = UserStatus.active
            user.email_verified = True
            user.email_verified_at = datetime.now(timezone.utc)
            user.is_active = True
            print(f"✅ Activated: {user.email}")
        
        await db.commit()
        print(f"\n✅ All {len(users)} users activated successfully!")


def main():
    parser = argparse.ArgumentParser(description="Activate PRISM users")
    parser.add_argument("--email", help="Email of user to activate")
    parser.add_argument("--list-pending", action="store_true", help="List all pending users")
    parser.add_argument("--activate-all", action="store_true", help="Activate all pending users")
    
    args = parser.parse_args()
    
    if args.list_pending:
        asyncio.run(list_pending_users())
    elif args.activate_all:
        response = input("⚠️  This will activate ALL pending users. Continue? (y/N): ")
        if response.lower() == 'y':
            asyncio.run(activate_all_pending())
        else:
            print("Cancelled")
    elif args.email:
        asyncio.run(activate_user(args.email))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()