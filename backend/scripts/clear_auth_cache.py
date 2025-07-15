#!/usr/bin/env python3
"""
Script to clear authentication-related cache and rate limiting data from Redis.
Useful for debugging authentication issues.
"""

import asyncio
import sys
from redis import asyncio as aioredis

# Default Redis connection
REDIS_URL = "redis://:redis_password@localhost:6380/0"


async def clear_auth_cache(redis_url: str = REDIS_URL):
    """Clear all authentication-related data from Redis."""
    
    redis = await aioredis.from_url(redis_url, decode_responses=True)
    
    try:
        print("Connecting to Redis...")
        await redis.ping()
        print("Connected successfully!")
        
        # Patterns to clear
        patterns = [
            "rate_limit:*",           # Rate limiting keys
            "ddos_pattern:*",         # DDoS protection keys
            "blocked:*",              # Blocked IPs
            "refresh_token:*",        # Refresh token families
            "blacklist:*",            # Token blacklist
            "auth:*",                 # General auth cache
        ]
        
        total_deleted = 0
        
        for pattern in patterns:
            print(f"\nSearching for keys matching: {pattern}")
            keys = []
            
            # Use SCAN to find all matching keys
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                print(f"Found {len(keys)} keys")
                # Delete in batches
                batch_size = 1000
                for i in range(0, len(keys), batch_size):
                    batch = keys[i:i + batch_size]
                    deleted = await redis.delete(*batch)
                    total_deleted += deleted
                    print(f"  Deleted {deleted} keys")
            else:
                print("  No keys found")
        
        print(f"\nTotal keys deleted: {total_deleted}")
        
        # Also clear specific problematic IPs if provided
        if len(sys.argv) > 1:
            ip = sys.argv[1]
            print(f"\nClearing specific IP: {ip}")
            
            specific_patterns = [
                f"rate_limit:*:{ip}",
                f"ddos_pattern:*:{ip}",
                f"blocked:{ip}",
            ]
            
            for pattern in specific_patterns:
                async for key in redis.scan_iter(match=pattern):
                    await redis.delete(key)
                    print(f"  Deleted: {key}")
        
        print("\nCache cleared successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await redis.close()


if __name__ == "__main__":
    print("Redis Auth Cache Cleaner")
    print("=" * 50)
    
    if len(sys.argv) > 2:
        redis_url = sys.argv[2]
    else:
        redis_url = REDIS_URL
    
    asyncio.run(clear_auth_cache(redis_url))