"""
Simplified project schemas for the current implementation.
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class ProjectCreateSimple(BaseModel):
    """Simple schema for creating a project."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    key: str = Field(..., min_length=2, max_length=10, pattern="^[A-Z][A-Z0-9]*$", description="Project key")
    description: Optional[str] = Field(None, max_length=2000)
    status: str = Field("planning", description="Project status")
    organization_id: int = Field(..., description="Organization ID")
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None


class ProjectUpdateSimple(BaseModel):
    """Simple schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = None
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None