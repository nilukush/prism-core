"""
Test health check endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_ready_check(client: AsyncClient):
    """Test readiness check endpoint."""
    response = await client.get("/ready")
    
    # The test might fail if services aren't running
    # but we can still check the response structure
    assert response.status_code in [200, 503]
    data = response.json()
    assert "ready" in data
    assert "checks" in data