#!/usr/bin/env python3
"""Direct database fix for user login issues."""

import psycopg2
import bcrypt
import sys

# Database connection for local Docker
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,  # Docker mapped port
    'database': 'prism_db',
    'user': 'prism',
    'password': 'prism_password'
}

def fix_user_login(email: str, new_password: str = 'test123'):
    """Fix user login by resetting status and password."""
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute("SELECT id, email, username, status, hashed_password FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if not user:
            print(f"❌ User '{email}' not found!")
            
            # List existing users
            cur.execute("SELECT email, username, status FROM users LIMIT 10")
            users = cur.fetchall()
            if users:
                print("\nExisting users:")
                for u in users:
                    print(f"  - {u[0]} (username: {u[1]}, status: {u[2]})")
            
            cur.close()
            conn.close()
            return
        
        print(f"\n✅ User found!")
        print(f"  Email: {user[1]}")
        print(f"  Username: {user[2]}")
        print(f"  Status: {user[3]}")
        
        # Generate new password hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        
        # Update user
        update_query = """
            UPDATE users 
            SET hashed_password = %s,
                status = 'active',
                email_verified = true,
                is_active = true,
                is_deleted = false,
                failed_login_attempts = 0,
                locked_until = null,
                updated_at = CURRENT_TIMESTAMP
            WHERE email = %s
        """
        
        cur.execute(update_query, (hashed.decode('utf-8'), email))
        conn.commit()
        
        print(f"\n🔧 User fixed successfully!")
        print(f"  New password: {new_password}")
        
        # Verify the update
        cur.execute("SELECT status, email_verified, is_active FROM users WHERE email = %s", (email,))
        result = cur.fetchone()
        print(f"\n📊 Final status:")
        print(f"  Status: {result[0]}")
        print(f"  Email verified: {result[1]}")
        print(f"  Is active: {result[2]}")
        
        # Test password
        is_valid = bcrypt.checkpw(new_password.encode('utf-8'), hashed)
        print(f"  Password verification: {'✅ Success' if is_valid else '❌ Failed'}")
        
        print(f"\n🎉 You can now login with:")
        print(f"  Email: {email}")
        print(f"  Password: {new_password}")
        print(f"  URL: http://localhost:8100")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_login_direct.py <email> [password]")
        print("Example: python fix_login_direct.py tomer.givoni.co@gmail.com test123")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else 'test123'
    
    print(f"🔧 Fixing login for user: {email}")
    fix_user_login(email, password)