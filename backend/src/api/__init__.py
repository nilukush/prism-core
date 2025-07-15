"""
API package initialization.
Combines all API routers into a single router.
"""

from fastapi import APIRouter

from backend.src.api.v1.router import api_v1_router
# from backend.src.api.graphql import graphql_router

# Create main API router
api_router = APIRouter()

# Include versioned API routers
api_router.include_router(api_v1_router)

# Include GraphQL router
# api_router.include_router(graphql_router, prefix="/graphql", tags=["graphql"])

__all__ = ["api_router"]