"""
Pytest configuration and fixtures.
"""

import asyncio
import pytest
from typing import AsyncGenerator

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from backend.src.core.config import settings
from backend.src.core.database import get_db
from backend.src.main import app
from backend.src.models.base import Base


# Override settings for testing
settings.DATABASE_URL = settings.TEST_DATABASE_URL or "postgresql+asyncpg://prism:prism_password@localhost:5432/prism_test"
settings.REDIS_URL = settings.TEST_REDIS_URL or "redis://localhost:6379/15"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client: AsyncClient) -> AsyncClient:
    """Create an authenticated test client."""
    # TODO: Implement authentication
    # For now, return the regular client
    return client