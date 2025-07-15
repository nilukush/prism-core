"""
GraphQL router configuration.
Sets up GraphQL endpoint with authentication and context.
"""

from typing import Any, Dict, Optional
from fastapi import Depends, Request, WebSocket, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.core.database import get_db
from backend.src.api.deps import get_current_user_optional
from backend.src.models.user import User
from .schema import schema
import logging

logger = logging.getLogger(__name__)

# Optional Bearer token for GraphQL
security = HTTPBearer(auto_error=False)


async def get_context(
    request: Request = None,
    websocket: WebSocket = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Create GraphQL context with database session and current user.
    """
    # Get current user if authenticated
    current_user = None
    if credentials:
        try:
            current_user = await get_current_user_optional(
                token=credentials.credentials,
                db=db
            )
        except Exception as e:
            logger.warning(f"Failed to authenticate GraphQL user: {e}")
    
    return {
        "request": request,
        "websocket": websocket,
        "background_tasks": background_tasks,
        "db": db,
        "current_user": current_user,
    }


# Create GraphQL router
graphql_router = GraphQLRouter(
    schema=schema,
    context_getter=get_context,
    graphiql=True,  # Enable GraphiQL playground in development
)