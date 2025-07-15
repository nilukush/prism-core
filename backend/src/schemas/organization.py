"""
Organization-related Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic.types import conint

from backend.src.schemas.common import TimestampMixin, PaginatedResponse


class OrganizationPlan(str, Enum):
    """Organization subscription plan."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class OrganizationStatus(str, Enum):
    """Organization status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str = Field(min_length=1, max_length=255, description="Organization name")
    slug: Optional[str] = Field(default=None, pattern="^[a-z0-9-]+$", description="URL-friendly slug")
    description: Optional[str] = Field(default=None, max_length=1000)
    website: Optional[str] = Field(default=None, max_length=255)
    logo_url: Optional[str] = Field(default=None)
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    industry: Optional[str] = Field(default=None, max_length=100)
    size: Optional[str] = Field(default=None, description="Company size range")
    country: Optional[str] = Field(default=None, max_length=2, description="ISO country code")
    
    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str], values: dict) -> Optional[str]:
        """Generate slug from name if not provided."""
        if not v and "name" in values:
            import re
            # Convert to lowercase and replace spaces/special chars with hyphens
            slug = re.sub(r'[^\w\s-]', '', values["name"].lower())
            slug = re.sub(r'[-\s]+', '-', slug).strip('-')
            return slug
        return v


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    website: Optional[str] = Field(default=None, max_length=255)
    logo_url: Optional[str] = None
    industry: Optional[str] = Field(default=None, max_length=100)
    size: Optional[str] = None
    country: Optional[str] = Field(default=None, max_length=2)
    settings: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationResponse(OrganizationBase, TimestampMixin):
    """Organization response schema."""
    id: UUID
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    plan: OrganizationPlan = OrganizationPlan.FREE
    industry: Optional[str] = None
    size: Optional[str] = None
    country: Optional[str] = None
    member_count: int = Field(default=0, description="Number of members")
    workspace_count: int = Field(default=0, description="Number of workspaces")
    settings: Dict[str, Any] = Field(default_factory=dict)
    owner_id: UUID
    subscription_expires_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(PaginatedResponse[OrganizationResponse]):
    """Paginated organization list response."""
    pass


class OrganizationStats(BaseModel):
    """Organization statistics."""
    total_members: int = Field(description="Total number of members")
    active_members: int = Field(description="Number of active members")
    total_workspaces: int = Field(description="Total number of workspaces")
    total_projects: int = Field(description="Total number of projects")
    total_stories: int = Field(description="Total number of stories")
    total_documents: int = Field(description="Total number of documents")
    total_ai_agents: int = Field(description="Total number of AI agents")
    storage_used_mb: float = Field(description="Storage used in MB")
    api_calls_this_month: int = Field(description="API calls this month")
    ai_tokens_used_this_month: int = Field(description="AI tokens used this month")
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationMember(BaseModel):
    """Organization member schema."""
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: str = Field(description="Member role in organization")
    joined_at: datetime
    invited_by: Optional[UUID] = None
    is_owner: bool = False
    
    # User details
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    last_active: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationInvite(BaseModel):
    """Organization invite schema."""
    email: str = Field(description="Email to invite")
    role: str = Field(default="member", description="Role to assign")
    message: Optional[str] = Field(default=None, max_length=500)
    workspace_ids: Optional[List[UUID]] = Field(default=None, description="Workspaces to add member to")