"""
Fixed database configuration using asyncpg properly.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from backend.src.core.config import settings

# IMPORTANT: Ensure the DATABASE_URL uses postgresql+asyncpg:// prefix
database_url = str(settings.DATABASE_URL)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine with asyncpg
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