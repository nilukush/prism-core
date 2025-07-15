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

# Create async engine
engine = create_async_engine(
    str(settings.DATABASE_URL),
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
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database by creating all tables."""
    from backend.src.models.base import Base
    # Import all models to register them with SQLAlchemy
    from backend.src.models import (
        User, Role, Permission,
        Organization, OrganizationMember, Team, TeamMember,
        Workspace, WorkspaceMember,
        Agent, AgentVersion, AgentExecution,
        Project, Sprint, Epic,
        Story, StoryComment, StoryAttachment,
        Document, DocumentVersion, DocumentTemplate,
        Integration, IntegrationConfig
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()