#!/usr/bin/env python3
"""
PRISM Connection Verification Script
Tests Neon PostgreSQL and Upstash Redis connections
"""

import os
import sys
import asyncio
import psycopg2
import httpx
from datetime import datetime

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header():
    print(f"\n{BLUE}{'='*50}")
    print("PRISM Connection Verification")
    print(f"{'='*50}{RESET}\n")

def test_neon_connection(database_url):
    """Test Neon PostgreSQL connection"""
    print(f"{BLUE}Testing Neon PostgreSQL...{RESET}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Test query
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"{GREEN}✓ Connected to PostgreSQL{RESET}")
        print(f"  Version: {version.split(',')[0]}")
        
        # Check tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        if tables:
            print(f"{GREEN}✓ Found {len(tables)} tables:{RESET}")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print(f"{YELLOW}⚠ No tables found. Run database migrations.{RESET}")
        
        # Check for admin user
        cur.execute("SELECT COUNT(*) FROM users WHERE email = 'admin@example.com';")
        admin_exists = cur.fetchone()[0] > 0
        
        if admin_exists:
            print(f"{GREEN}✓ Admin user exists{RESET}")
        else:
            print(f"{YELLOW}⚠ Admin user not found. Initialize database.{RESET}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"{RED}✗ PostgreSQL connection failed:{RESET}")
        print(f"  {str(e)}")
        return False

async def test_upstash_connection(redis_url, redis_token):
    """Test Upstash Redis connection"""
    print(f"\n{BLUE}Testing Upstash Redis...{RESET}")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test PING command
            response = await client.post(
                redis_url,
                json=["PING"],
                headers={"Authorization": f"Bearer {redis_token}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result") == "PONG":
                    print(f"{GREEN}✓ Connected to Redis{RESET}")
                    
                    # Test SET/GET
                    test_key = "prism:test:connection"
                    test_value = f"Connected at {datetime.now().isoformat()}"
                    
                    # SET
                    await client.post(
                        redis_url,
                        json=["SET", test_key, test_value],
                        headers={"Authorization": f"Bearer {redis_token}"}
                    )
                    
                    # GET
                    response = await client.post(
                        redis_url,
                        json=["GET", test_key],
                        headers={"Authorization": f"Bearer {redis_token}"}
                    )
                    
                    stored_value = response.json().get("result")
                    if stored_value == test_value:
                        print(f"{GREEN}✓ SET/GET operations working{RESET}")
                    
                    # Check info
                    response = await client.post(
                        redis_url,
                        json=["INFO", "server"],
                        headers={"Authorization": f"Bearer {redis_token}"}
                    )
                    
                    info = response.json().get("result", "")
                    if "upstash" in info.lower():
                        print(f"{GREEN}✓ Upstash Redis confirmed{RESET}")
                    
                    return True
            else:
                print(f"{RED}✗ Redis connection failed: HTTP {response.status_code}{RESET}")
                return False
                
    except Exception as e:
        print(f"{RED}✗ Redis connection failed:{RESET}")
        print(f"  {str(e)}")
        return False

def check_environment():
    """Check environment variables"""
    print(f"{BLUE}Checking environment variables...{RESET}")
    
    required_vars = {
        "DATABASE_URL": "PostgreSQL connection string",
        "UPSTASH_REDIS_REST_URL": "Upstash REST API URL",
        "UPSTASH_REDIS_REST_TOKEN": "Upstash REST API token",
        "SECRET_KEY": "Application secret key",
        "JWT_SECRET_KEY": "JWT signing key"
    }
    
    missing = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "TOKEN" in var or "SECRET" in var or "KEY" in var:
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"{GREEN}✓ {var}: {masked}{RESET}")
            elif "URL" in var:
                # Show partial URL
                if "postgresql" in value:
                    parts = value.split("@")
                    if len(parts) > 1:
                        masked = "postgresql://***@" + parts[1]
                    else:
                        masked = value[:20] + "..."
                else:
                    masked = value[:30] + "..." if len(value) > 30 else value
                print(f"{GREEN}✓ {var}: {masked}{RESET}")
            else:
                print(f"{GREEN}✓ {var}: Set{RESET}")
        else:
            print(f"{RED}✗ {var}: Not set ({description}){RESET}")
            missing.append(var)
    
    return len(missing) == 0

async def main():
    """Main verification process"""
    print_header()
    
    # Load environment
    if os.path.exists('.env.production'):
        print(f"{BLUE}Loading .env.production...{RESET}")
        from dotenv import load_dotenv
        load_dotenv('.env.production')
        print(f"{GREEN}✓ Environment loaded{RESET}\n")
    
    # Check environment variables
    env_ok = check_environment()
    
    if not env_ok:
        print(f"\n{RED}Please set all required environment variables!{RESET}")
        sys.exit(1)
    
    # Test connections
    print(f"\n{BLUE}Testing connections...{RESET}")
    
    # Test PostgreSQL
    db_ok = test_neon_connection(os.getenv("DATABASE_URL"))
    
    # Test Redis
    redis_ok = await test_upstash_connection(
        os.getenv("UPSTASH_REDIS_REST_URL"),
        os.getenv("UPSTASH_REDIS_REST_TOKEN")
    )
    
    # Summary
    print(f"\n{BLUE}{'='*50}{RESET}")
    print(f"{BLUE}Summary:{RESET}")
    print(f"{'='*50}")
    
    if db_ok and redis_ok:
        print(f"{GREEN}✓ All connections successful!{RESET}")
        print(f"\n{GREEN}Your PRISM deployment is ready to go! 🚀{RESET}")
    else:
        print(f"{RED}✗ Some connections failed.{RESET}")
        print(f"{YELLOW}Please check the error messages above.{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print(f"{RED}Python 3.7+ required{RESET}")
        sys.exit(1)
    
    # Install required packages if missing
    try:
        import psycopg2
        import httpx
        import dotenv
    except ImportError as e:
        print(f"{YELLOW}Installing required packages...{RESET}")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "httpx", "python-dotenv"])
        print(f"{GREEN}✓ Packages installed. Please run the script again.{RESET}")
        sys.exit(0)
    
    # Run verification
    asyncio.run(main())