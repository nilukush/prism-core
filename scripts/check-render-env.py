#!/usr/bin/env python3
"""Check environment variables in Render deployment."""

import os
import sys

print("=== Checking Render Environment Variables ===")
print()

# Critical environment variables to check
critical_vars = [
    "DATABASE_URL",
    "REDIS_URL",
    "UPSTASH_REDIS_REST_URL",
    "UPSTASH_REDIS_REST_TOKEN",
    "QDRANT_URL",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEFAULT_LLM_PROVIDER",
    "SECRET_KEY",
]

# Check each variable
missing_vars = []
for var in critical_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if "KEY" in var or "TOKEN" in var or "SECRET" in var:
            masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✅ {var}: {masked_value}")
        elif "URL" in var:
            # Show URL without password
            if "@" in value:
                parts = value.split("@")
                if len(parts) > 1:
                    scheme_user = parts[0].split("://")
                    if len(scheme_user) > 1:
                        scheme = scheme_user[0]
                        user_parts = scheme_user[1].split(":")
                        if len(user_parts) > 1:
                            user = user_parts[0]
                            masked_value = f"{scheme}://{user}:***@{parts[1]}"
                        else:
                            masked_value = value
                    else:
                        masked_value = value
                else:
                    masked_value = value
            else:
                masked_value = value
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"✅ {var}: {value}")
    else:
        print(f"❌ {var}: Not set")
        missing_vars.append(var)

print()

# Check for common issues
if "DATABASE_URL" in os.environ:
    db_url = os.environ["DATABASE_URL"]
    if "sslmode=" in db_url:
        print("⚠️  DATABASE_URL contains sslmode parameter - this may cause issues with asyncpg")
    if not db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
        print("⚠️  DATABASE_URL doesn't start with postgresql:// or postgresql+asyncpg://")

if "REDIS_URL" in os.environ:
    redis_url = os.environ["REDIS_URL"]
    if redis_url == "redis://localhost:6379/0":
        print("⚠️  REDIS_URL is set to localhost - should be Upstash URL")
    elif "upstash" not in redis_url and not os.getenv("UPSTASH_REDIS_REST_URL"):
        print("⚠️  Neither REDIS_URL contains 'upstash' nor UPSTASH_REDIS_REST_URL is set")

print()
if missing_vars:
    print(f"❌ Missing {len(missing_vars)} critical environment variables:")
    for var in missing_vars:
        print(f"   - {var}")
    sys.exit(1)
else:
    print("✅ All critical environment variables are set!")