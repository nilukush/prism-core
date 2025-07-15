"""
Request ID middleware for request tracing.
"""

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with unique ID."""
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Bind request ID to context
        bind_contextvars(request_id=request_id)
        
        # Store in request state
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
        finally:
            # Clear context
            clear_contextvars()