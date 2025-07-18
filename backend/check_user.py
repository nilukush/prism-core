"""Quick script to check user status and fix login issues."""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Add asyncpg for async
if "postgresql://" in DATABASE_URL and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

print(f"Using database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Not configured'}")

from sqlalchemy import select, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import bcrypt


async def check_user(email: str):
    """Check user status in database."""
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Raw SQL to check user
        result = await session.execute(
            f"SELECT id, email, username, status, email_verified, is_active, is_deleted, failed_login_attempts, locked_until, hashed_password FROM users WHERE email = '{email}'"
        )
        user = result.fetchone()
        
        if not user:
            print(f"\n❌ User '{email}' not found!")
            
            # List all users
            all_users = await session.execute("SELECT email, username, status FROM users")
            users_list = all_users.fetchall()
            
            if users_list:
                print("\nExisting users:")
                for u in users_list:
                    print(f"  - {u[0]} (username: {u[1]}, status: {u[2]})")
            return
        
        print(f"\n✅ User found!")
        print(f"  ID: {user[0]}")
        print(f"  Email: {user[1]}")
        print(f"  Username: {user[2]}")
        print(f"  Status: {user[3]}")
        print(f"  Email verified: {user[4]}")
        print(f"  Is active: {user[5]}")
        print(f"  Is deleted: {user[6]}")
        print(f"  Failed attempts: {user[7]}")
        print(f"  Locked until: {user[8]}")
        
        # Check password
        hashed_password = user[9]
        if hashed_password:
            test_passwords = ["test123", "Test123!", "password", "Password123!"]
            print(f"\nTesting common passwords...")
            for pwd in test_passwords:
                try:
                    is_valid = bcrypt.checkpw(pwd.encode('utf-8'), hashed_password.encode('utf-8'))
                    if is_valid:
                        print(f"  ✅ Password '{pwd}' is valid!")
                        break
                except Exception as e:
                    print(f"  ❌ Error testing '{pwd}': {e}")
            else:
                print("  ❌ None of the common passwords worked")
        
        # Fix user if needed
        if user[3] != 'active' or not user[4] or not user[5]:
            print("\n🔧 Fixing user status...")
            await session.execute(
                f"""UPDATE users 
                SET status = 'active', 
                    email_verified = true, 
                    is_active = true, 
                    is_deleted = false,
                    failed_login_attempts = 0,
                    locked_until = null
                WHERE email = '{email}'"""
            )
            await session.commit()
            print("✅ User status fixed!")
    
    await engine.dispose()


async def reset_password(email: str, new_password: str):
    """Reset user password."""
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Generate new password hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        
        # Update password
        await session.execute(
            f"""UPDATE users 
            SET hashed_password = '{hashed.decode('utf-8')}',
                status = 'active',
                email_verified = true,
                is_active = true,
                is_deleted = false,
                failed_login_attempts = 0,
                locked_until = null
            WHERE email = '{email}'"""
        )
        await session.commit()
        
        print(f"\n✅ Password reset successfully!")
        print(f"  Email: {email}")
        print(f"  New password: {new_password}")
        
        # Verify it works
        is_valid = bcrypt.checkpw(new_password.encode('utf-8'), hashed)
        print(f"  Verification: {'✅ Success' if is_valid else '❌ Failed'}")
    
    await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["check", "reset"])
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", help="New password for reset")
    
    args = parser.parse_args()
    
    if args.command == "check":
        asyncio.run(check_user(args.email))
    elif args.command == "reset":
        if not args.password:
            print("❌ Password required for reset command")
            sys.exit(1)
        asyncio.run(reset_password(args.email, args.password))