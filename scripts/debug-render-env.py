#!/usr/bin/env python3
"""
Debug script to check environment variables in Render deployment.
This script should be run inside the deployed container to verify environment setup.
"""

import os
import sys
from urllib.parse import urlparse, parse_qs

def check_env_var(name, required=True):
    """Check if an environment variable exists and print its status."""
    value = os.environ.get(name)
    if value:
        # Mask sensitive parts of the value
        if "DATABASE_URL" in name or "REDIS" in name or "API_KEY" in name:
            # Show only the beginning for debugging
            masked = value[:20] + "..." if len(value) > 20 else value
            print(f"✓ {name}: Set (masked: {masked})")
        else:
            print(f"✓ {name}: {value}")
        return value
    else:
        status = "✗ MISSING (REQUIRED)" if required else "✗ Missing (optional)"
        print(f"{status}: {name}")
        return None

def parse_database_url(url):
    """Parse and validate DATABASE_URL format."""
    if not url:
        return
    
    print("\nDATABASE_URL Analysis:")
    try:
        parsed = urlparse(url)
        print(f"  - Scheme: {parsed.scheme}")
        print(f"  - Host: {parsed.hostname}")
        print(f"  - Port: {parsed.port}")
        print(f"  - Database: {parsed.path.lstrip('/')}")
        
        # Check for query parameters (like sslmode)
        if parsed.query:
            print(f"  - Query params: {parsed.query}")
            params = parse_qs(parsed.query)
            for key, values in params.items():
                print(f"    - {key}: {values}")
        
        # Check if the URL has malformed sslmode
        if "&channel_binding=" in url or "&sslmode=" in parsed.path:
            print("  ⚠️  WARNING: sslmode parameters may be incorrectly placed in the database name!")
            print("  ⚠️  The database name appears to include query parameters")
            
    except Exception as e:
        print(f"  ✗ Error parsing DATABASE_URL: {e}")

def check_redis_config():
    """Check Redis configuration."""
    redis_url = os.environ.get("REDIS_URL")
    upstash_redis_rest_url = os.environ.get("UPSTASH_REDIS_REST_URL")
    upstash_redis_rest_token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    
    print("\nRedis Configuration:")
    if redis_url:
        print(f"  - REDIS_URL is set")
        parsed = urlparse(redis_url)
        print(f"    - Host: {parsed.hostname}")
        print(f"    - Port: {parsed.port}")
        if parsed.hostname == "localhost":
            print("  ⚠️  WARNING: Redis is configured to use localhost - this won't work in production!")
    
    if upstash_redis_rest_url:
        print(f"  - UPSTASH_REDIS_REST_URL is set")
    else:
        print("  ✗ UPSTASH_REDIS_REST_URL is not set")
        
    if upstash_redis_rest_token:
        print(f"  - UPSTASH_REDIS_REST_TOKEN is set")
    else:
        print("  ✗ UPSTASH_REDIS_REST_TOKEN is not set")

def main():
    print("=== PRISM Backend Environment Variable Check ===\n")
    
    # Core environment
    print("Core Configuration:")
    check_env_var("ENVIRONMENT", required=False)
    check_env_var("PORT", required=False)
    check_env_var("SECRET_KEY")
    
    # Database
    print("\nDatabase Configuration:")
    db_url = check_env_var("DATABASE_URL")
    parse_database_url(db_url)
    
    # Redis/Cache
    check_redis_config()
    
    # Vector Store
    print("\nVector Store Configuration:")
    check_env_var("QDRANT_HOST", required=False)
    check_env_var("QDRANT_PORT", required=False)
    check_env_var("QDRANT_API_KEY", required=False)
    
    # AI/LLM Keys
    print("\nAI/LLM Configuration:")
    check_env_var("OPENAI_API_KEY", required=False)
    check_env_var("ANTHROPIC_API_KEY", required=False)
    
    # Auth
    print("\nAuthentication Configuration:")
    check_env_var("JWT_SECRET_KEY", required=False)
    check_env_var("JWT_ALGORITHM", required=False)
    
    # Monitoring
    print("\nMonitoring Configuration:")
    check_env_var("SENTRY_DSN", required=False)
    check_env_var("DD_API_KEY", required=False)
    
    print("\n=== Recommendations ===")
    
    # Database URL fix
    if db_url and "&channel_binding=" in db_url:
        print("\n1. Fix DATABASE_URL format:")
        print("   The database URL seems to have query parameters in the wrong place.")
        print("   Correct format: postgresql://user:pass@host:port/database?sslmode=require")
        print("   Your URL might have: postgresql://user:pass@host:port/database&sslmode=require")
        print("   Note the '?' vs '&' difference")
    
    # Redis configuration
    if not os.environ.get("UPSTASH_REDIS_REST_URL"):
        print("\n2. Configure Upstash Redis:")
        print("   - Set UPSTASH_REDIS_REST_URL from your Upstash dashboard")
        print("   - Set UPSTASH_REDIS_REST_TOKEN from your Upstash dashboard")
        print("   - Or set REDIS_URL to a proper Redis instance URL (not localhost)")
    
    # Vector store
    if not os.environ.get("QDRANT_HOST"):
        print("\n3. Configure Qdrant (optional):")
        print("   - Set QDRANT_HOST, QDRANT_PORT, and QDRANT_API_KEY")
        print("   - Or the app will run without vector store functionality")

if __name__ == "__main__":
    main()