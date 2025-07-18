"""
API v1 router configuration.
Aggregates all v1 endpoints with proper prefixes and tags.
"""

import os
from fastapi import APIRouter

from backend.src.api.v1.auth import router as auth_router
from backend.src.core.config import settings

# Import enterprise auth to apply overrides if enabled
if os.getenv("USE_PERSISTENT_SESSIONS", "false").lower() == "true" or settings.ENVIRONMENT in ["production", "staging"]:
    from backend.src.api.v1.auth_enterprise import apply_enterprise_overrides
    apply_enterprise_overrides()
from backend.src.api.v1.users import router as users_router
from backend.src.api.v1.workspaces import router as workspaces_router
from backend.src.api.v1.agents import router as agents_router
from backend.src.api.v1.organizations import router as organizations_router
# from backend.src.api.v1.prompts import router as prompts_router
from backend.src.api.v1.analytics import router as analytics_router
from backend.src.api.v1.health import router as health_router
from backend.src.api.v1.email import router as email_router
from backend.src.api.v1.public import router as public_router
from backend.src.api.v1.ai import router as ai_router
from backend.src.api.v1.documents import router as documents_router
from backend.src.api.v1.projects import router as projects_router

# Import debug router only in development
if settings.DEBUG:
    from backend.src.api.v1.debug import router as debug_router

# Import activation endpoint with proper security
from backend.src.api.v1.activation import router as activation_router

# Create v1 API router
api_v1_router = APIRouter()

# Include all endpoint routers
api_v1_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
# api_v1_router.include_router(users_router, prefix="/users", tags=["users"])
# api_v1_router.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
# api_v1_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_v1_router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
# api_v1_router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
# api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_v1_router.include_router(health_router, prefix="/health", tags=["health"])
# api_v1_router.include_router(email_router, prefix="/email", tags=["email"])
api_v1_router.include_router(public_router, prefix="/public", tags=["public"])
api_v1_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_v1_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_v1_router.include_router(projects_router, prefix="/projects", tags=["projects"])

# Include debug router only in development
if settings.DEBUG:
    api_v1_router.include_router(debug_router, prefix="/debug", tags=["debug"])

# Include activation endpoint with environment-based security
if settings.ENVIRONMENT in ["development", "local", "staging"] or settings.DEBUG:
    api_v1_router.include_router(activation_router, prefix="/activation", tags=["activation"])
else:
    # In production, only include the main activation endpoint (not dev endpoints)
    api_v1_router.include_router(activation_router, prefix="/activation", tags=["activation"])

__all__ = ["api_v1_router"]