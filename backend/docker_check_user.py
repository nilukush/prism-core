#!/usr/bin/env python3
"""Check and fix user login issues in Docker environment."""

import os
import sys
import asyncio
import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Database configuration for Docker
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://prism:prism_password@localhost:5432/prism_db")
print(f"🔗 Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Not configured'}")


async def check_and_fix_user(email: str, new_password: str = None):
    """Check user status and optionally reset password."""
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user exists
        result = await session.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": email}
        )
        user = result.fetchone()
        
        if not user:
            print(f"\n❌ User '{email}' not found!")
            
            # List all users
            all_users = await session.execute(text("SELECT email, username, status FROM users"))
            users_list = all_users.fetchall()
            
            if users_list:
                print("\n📋 Existing users:")
                for u in users_list:
                    print(f"  - {u.email} (username: {u.username}, status: {u.status})")
            else:
                print("\n❌ No users in database!")
            return
        
        # Display user info
        print(f"\n✅ User found!")
        print(f"  Email: {user.email}")
        print(f"  Username: {user.username}")
        print(f"  Status: {user.status}")
        print(f"  Email verified: {user.email_verified}")
        print(f"  Is active: {user.is_active}")
        print(f"  Failed attempts: {user.failed_login_attempts}")
        
        # Test current password
        if user.hashed_password:
            test_passwords = ["test123", "Test123!", "password123", "Password123!"]
            print(f"\n🔑 Testing passwords...")
            for pwd in test_passwords:
                try:
                    is_valid = bcrypt.checkpw(pwd.encode('utf-8'), user.hashed_password.encode('utf-8'))
                    if is_valid:
                        print(f"  ✅ Current password is: '{pwd}'")
                        break
                except Exception as e:
                    pass
            else:
                print("  ❌ Could not verify current password")
        
        # Fix user status
        print("\n🔧 Fixing user status...")
        await session.execute(
            text("""UPDATE users 
                 SET status = 'active', 
                     email_verified = true, 
                     is_active = true, 
                     is_deleted = false,
                     failed_login_attempts = 0,
                     locked_until = null
                 WHERE email = :email"""),
            {"email": email}
        )
        
        # Reset password if requested
        if new_password:
            print(f"\n🔐 Setting new password: '{new_password}'")
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), salt)
            
            await session.execute(
                text("UPDATE users SET hashed_password = :password WHERE email = :email"),
                {"password": hashed.decode('utf-8'), "email": email}
            )
            
            # Verify new password
            is_valid = bcrypt.checkpw(new_password.encode('utf-8'), hashed)
            print(f"  Verification: {'✅ Success' if is_valid else '❌ Failed'}")
        
        await session.commit()
        print("\n✅ User fixed successfully!")
        
        # Show final status
        result = await session.execute(
            text("SELECT email, status, email_verified, is_active FROM users WHERE email = :email"),
            {"email": email}
        )
        final_user = result.fetchone()
        print(f"\n📊 Final status:")
        print(f"  Email: {final_user.email}")
        print(f"  Status: {final_user.status}")
        print(f"  Email verified: {final_user.email_verified}")
        print(f"  Is active: {final_user.is_active}")
        
        if new_password:
            print(f"\n🎉 You can now login with:")
            print(f"  Email: {email}")
            print(f"  Password: {new_password}")
    
    await engine.dispose()


async def create_test_user(email: str, password: str):
    """Create a test user."""
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if exists
        result = await session.execute(
            text("SELECT email FROM users WHERE email = :email"),
            {"email": email}
        )
        if result.fetchone():
            print(f"❌ User '{email}' already exists!")
            return
        
        # Create user
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        username = email.split('@')[0]
        
        await session.execute(
            text("""INSERT INTO users 
                 (email, username, hashed_password, status, email_verified, is_active, is_deleted, failed_login_attempts)
                 VALUES (:email, :username, :password, 'active', true, true, false, 0)"""),
            {
                "email": email,
                "username": username,
                "password": hashed.decode('utf-8')
            }
        )
        await session.commit()
        
        print(f"\n✅ User created successfully!")
        print(f"  Email: {email}")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
    
    await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix user login issues")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Check/fix command
    check_parser = subparsers.add_parser("fix", help="Check and fix user")
    check_parser.add_argument("email", help="User email")
    check_parser.add_argument("--password", help="New password to set")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create test user")
    create_parser.add_argument("email", help="User email")
    create_parser.add_argument("password", help="User password")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "fix":
        asyncio.run(check_and_fix_user(args.email, args.password))
    elif args.command == "create":
        asyncio.run(create_test_user(args.email, args.password))