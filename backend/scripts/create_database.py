#!/usr/bin/env python3
"""
Script to create the database if it doesn't exist.
Run this before running migrations.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncpg
from sqlalchemy.engine.url import make_url

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


async def create_database():
    """Create the database if it doesn't exist."""
    # Parse the database URL
    db_url = make_url(str(settings.DATABASE_URL))
    
    # Connect to the default 'postgres' database
    conn = await asyncpg.connect(
        host=db_url.host,
        port=db_url.port or 5432,
        user=db_url.username,
        password=db_url.password,
        database='postgres'
    )
    
    try:
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            db_url.database
        )
        
        if not exists:
            # Create the database
            await conn.execute(f'CREATE DATABASE "{db_url.database}"')
            logger.info(f"Database '{db_url.database}' created successfully")
        else:
            logger.info(f"Database '{db_url.database}' already exists")
            
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_database())