"""
Common schemas used across the application.
"""

from enum import Enum
from typing import Generic, List, Optional, TypeVar
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


T = TypeVar("T")


class SortDirection(str, Enum):
    """Sort direction enum."""
    ASC = "asc"
    DESC = "desc"


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps."""
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    """Pagination parameters."""
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items to return")
    

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int = Field(description="Number of items returned")
    items: List[T] = Field(description="List of items")
    
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str = Field(description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")
    field: Optional[str] = Field(default=None, description="Field that caused the error")


class SuccessResponse(BaseModel):
    """Success response schema."""
    message: str = Field(description="Success message")
    data: Optional[dict] = Field(default=None, description="Additional data")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Service status")
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Optional[dict] = Field(default=None, description="Additional health checks")