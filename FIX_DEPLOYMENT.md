# 🔧 PRISM Deployment Fixes

## Issue #1: Render Backend - `psycopg2` Error

### Root Cause
The database URL is not using the `asyncpg` prefix, causing SQLAlchemy to try loading `psycopg2` instead.

### Fix in Render Dashboard

1. **Go to Environment Variables** in Render
2. **Update DATABASE_URL**:
   - Current: `postgresql://neondb_owner:...`
   - Change to: `postgresql+asyncpg://neondb_owner:...`
   
   Full URL should be:
   ```
   postgresql+asyncpg://neondb_owner:npg_rQk92nifVozE@ep-tiny-grass-aet08v5u-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

3. **Save Changes** - Service will auto-restart

### Alternative Fix (Code Change)
If you can't change the URL, update the database.py file:

```python
# At line 18, before create_async_engine, add:
database_url = str(settings.DATABASE_URL)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Then use database_url instead of str(settings.DATABASE_URL)
engine = create_async_engine(
    database_url,  # <- Use modified URL
    # ... rest of config
)
```

## Issue #2: OpenAI API Key

Your API key is actually **VALID**! The error occurred because:
1. The key wasn't loaded in the test environment
2. The `openai` module isn't installed in the test environment

### Verify in Render
Make sure these are set in Environment Variables:
```
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk-proj-YOUR-OPENAI-API-KEY-HERE
```

## Issue #3: Vercel - Still Looking in Wrong Directory

### The Problem
Even though root directory is set to `frontend`, Vercel is still running `cd frontend && npm install`.

### Fix Options

#### Option A: Update package.json scripts
In your root `package.json`, remove any build/install commands that reference frontend.

#### Option B: Use Vercel CLI with explicit path
```bash
cd frontend
vercel --prod --confirm
```

#### Option C: Check Vercel Build Settings
In Vercel Dashboard:
1. Go to Project Settings → General
2. **Framework Preset**: Next.js
3. **Build Command**: `npm run build` (NOT `cd frontend && npm run build`)
4. **Output Directory**: `.next`
5. **Install Command**: `npm install` (NOT `cd frontend && npm install`)
6. **Development Command**: `npm run dev`

## Quick Fix Commands

### 1. Test Database Connection Locally
```bash
# Update your local .env with asyncpg prefix
sed -i '' 's|postgresql://|postgresql+asyncpg://|g' .env.production

# Test connection
python -c "
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

async def test():
    engine = create_async_engine('postgresql+asyncpg://neondb_owner:npg_rQk92nifVozE@ep-tiny-grass-aet08v5u-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require')
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('Database connection successful!')
    await engine.dispose()

asyncio.run(test())
"
```

### 2. Push Database Fix
```bash
# Create a quick fix
cat > backend/src/core/database.py << 'EOF'
"""
Database configuration and session management.
Uses SQLAlchemy with async support for PostgreSQL.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from backend.src.core.config import settings

# Fix for asyncpg driver
database_url = str(settings.DATABASE_URL)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine
engine = create_async_engine(
    database_url,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
    poolclass=NullPool if settings.is_testing else None,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    # Import all models to ensure they're registered
    from backend.src.models import (  # noqa: F401
        agent,
        base,
        chat,
        document,
        epic,
        integration,
        project,
        sprint,
        story,
        user,
        workspace,
    )
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(base.Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
EOF

# Commit and push
git add backend/src/core/database.py
git commit -m "Fix: Use asyncpg driver for PostgreSQL connection"
git push
```

## Immediate Action Plan

### 1. Fix Render (2 minutes)
Go to Render Dashboard → Environment → Update DATABASE_URL with `postgresql+asyncpg://` prefix

### 2. Fix Vercel (5 minutes)
1. Go to Vercel Dashboard → Project Settings
2. Check Build & Development Settings
3. Remove any `cd frontend` commands
4. Redeploy

### 3. Monitor Results
```bash
# Check Render
curl https://prism-backend-bwfx.onrender.com/health

# Once both are working, test full flow
curl https://prism-backend-bwfx.onrender.com/api/v1/ai/config/test
```

## Summary

1. **Render**: Just needs `+asyncpg` in the DATABASE_URL
2. **OpenAI**: Your key is valid, no action needed
3. **Vercel**: Remove the `cd frontend` from build commands

These are all simple configuration fixes that should take less than 10 minutes total!