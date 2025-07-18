#!/usr/bin/env python3
"""
Script to diagnose and fix user login issues.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.user import User, UserStatus
from src.core.security import get_password_hash, verify_password
from src.core.config import settings


async def diagnose_user(email: str, test_password: str = None):
    """Diagnose user login issues."""
    
    # Create database engine
    engine = create_async_engine(str(settings.DATABASE_URL), echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find user
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"\n❌ User with email '{email}' not found!")
            
            # List all users
            all_users_result = await session.execute(select(User))
            all_users = all_users_result.scalars().all()
            
            if all_users:
                print("\nExisting users:")
                for u in all_users:
                    print(f"  - {u.email} (username: {u.username}, status: {u.status})")
            else:
                print("\nNo users found in the database!")
            return
        
        # Display user info
        print(f"\n✅ User found!")
        print(f"  Email: {user.email}")
        print(f"  Username: {user.username}")
        print(f"  Status: {user.status}")
        print(f"  Email verified: {user.email_verified}")
        print(f"  Is active: {user.is_active}")
        print(f"  Is deleted: {user.is_deleted}")
        print(f"  Failed login attempts: {user.failed_login_attempts}")
        print(f"  Locked until: {user.locked_until}")
        print(f"  Created at: {user.created_at}")
        print(f"  Last login: {user.last_login_at}")
        
        # Check password if provided
        if test_password:
            print(f"\nTesting password '{test_password}'...")
            is_valid = verify_password(test_password, user.hashed_password)
            print(f"  Password valid: {is_valid}")
            
            if not is_valid:
                print("\n  ❌ Password verification failed!")
                print("  The password does not match the stored hash.")
        
        # Check for common issues
        print("\n🔍 Checking for common issues:")
        
        issues = []
        
        if user.status != UserStatus.active:
            issues.append(f"User status is '{user.status}', not 'active'")
        
        if not user.email_verified:
            issues.append("Email is not verified")
        
        if not user.is_active:
            issues.append("User is not active (is_active=False)")
        
        if user.is_deleted:
            issues.append("User is marked as deleted")
        
        if user.failed_login_attempts >= 5:
            issues.append(f"Too many failed login attempts ({user.failed_login_attempts})")
        
        if user.locked_until:
            issues.append(f"User is locked until {user.locked_until}")
        
        if issues:
            print("  Found issues:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("  ✅ No obvious issues found")
    
    await engine.dispose()


async def fix_user_login(email: str, new_password: str = None):
    """Fix user login issues by resetting status and optionally password."""
    
    # Create database engine
    engine = create_async_engine(str(settings.DATABASE_URL), echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find user
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"\n❌ User with email '{email}' not found!")
            return
        
        print(f"\n🔧 Fixing user: {email}")
        
        # Fix all common issues
        user.status = UserStatus.active
        user.email_verified = True
        user.is_active = True
        user.is_deleted = False
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Update password if provided
        if new_password:
            print(f"  Setting new password: {new_password}")
            user.hashed_password = get_password_hash(new_password)
            
            # Verify the new password works
            is_valid = verify_password(new_password, user.hashed_password)
            print(f"  Password verification: {'✅ Success' if is_valid else '❌ Failed'}")
        
        await session.commit()
        
        print("\n✅ User fixed successfully!")
        print(f"  Status: {user.status}")
        print(f"  Email verified: {user.email_verified}")
        print(f"  Is active: {user.is_active}")
        print(f"  Failed attempts: {user.failed_login_attempts}")
    
    await engine.dispose()


async def create_test_user(email: str, password: str, username: str = None):
    """Create a new test user."""
    
    # Create database engine
    engine = create_async_engine(str(settings.DATABASE_URL), echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"\n❌ User with email '{email}' already exists!")
            return
        
        # Create new user
        user = User(
            email=email,
            username=username or email.split('@')[0],
            hashed_password=get_password_hash(password),
            status=UserStatus.active,
            email_verified=True,
            is_active=True,
            is_deleted=False,
            failed_login_attempts=0
        )
        
        session.add(user)
        await session.commit()
        
        print(f"\n✅ User created successfully!")
        print(f"  Email: {user.email}")
        print(f"  Username: {user.username}")
        print(f"  Password: {password}")
        
        # Verify password
        is_valid = verify_password(password, user.hashed_password)
        print(f"  Password verification: {'✅ Success' if is_valid else '❌ Failed'}")
    
    await engine.dispose()


async def list_all_users():
    """List all users in the database."""
    
    # Create database engine
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("\n❌ No users found in the database!")
            return
        
        print(f"\n📋 Total users: {len(users)}")
        print("\nUsers:")
        for user in users:
            status_emoji = "✅" if user.status == UserStatus.active else "❌"
            print(f"  {status_emoji} {user.email}")
            print(f"     - Username: {user.username}")
            print(f"     - Status: {user.status}")
            print(f"     - Email verified: {user.email_verified}")
            print(f"     - Active: {user.is_active}")
            print(f"     - Created: {user.created_at}")
            print()
    
    await engine.dispose()


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix user login issues")
    parser.add_argument("command", choices=["diagnose", "fix", "create", "list"], 
                       help="Command to run")
    parser.add_argument("--email", help="User email address")
    parser.add_argument("--password", help="Password to test or set")
    parser.add_argument("--username", help="Username for new user")
    
    args = parser.parse_args()
    
    if args.command == "list":
        await list_all_users()
    elif args.command == "diagnose":
        if not args.email:
            print("❌ Email is required for diagnose command")
            sys.exit(1)
        await diagnose_user(args.email, args.password)
    elif args.command == "fix":
        if not args.email:
            print("❌ Email is required for fix command")
            sys.exit(1)
        await fix_user_login(args.email, args.password)
    elif args.command == "create":
        if not args.email or not args.password:
            print("❌ Email and password are required for create command")
            sys.exit(1)
        await create_test_user(args.email, args.password, args.username)


if __name__ == "__main__":
    # Check environment
    print(f"🔧 PRISM User Login Fix Tool")
    print(f"📍 Environment: {settings.APP_ENV}")
    print(f"🗄️  Database: {settings.DATABASE_URL.scheme}://***")
    print(f"🐛 Debug mode: {settings.APP_DEBUG}")
    print()
    
    asyncio.run(main())