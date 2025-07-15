"""
Workspace-related Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator

from backend.src.schemas.common import TimestampMixin, PaginatedResponse, SortDirection


class WorkspaceType(str, Enum):
    """Workspace type enum."""
    PRODUCT = "product"
    PROJECT = "project"
    TEAM = "team"
    PERSONAL = "personal"
    DEPARTMENT = "department"


class WorkspaceVisibility(str, Enum):
    """Workspace visibility."""
    PUBLIC = "public"  # Visible to all organization members
    PRIVATE = "private"  # Visible only to workspace members
    INTERNAL = "internal"  # Visible to specific teams


class MemberRole(str, Enum):
    """Workspace member role."""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    GUEST = "guest"


class WorkspaceBase(BaseModel):
    """Base workspace schema."""
    name: str = Field(min_length=1, max_length=255, description="Workspace name")
    slug: Optional[str] = Field(default=None, pattern="^[a-z0-9-]+$", description="URL-friendly slug")
    description: Optional[str] = Field(default=None, max_length=1000)
    type: WorkspaceType = Field(default=WorkspaceType.PROJECT)
    visibility: WorkspaceVisibility = Field(default=WorkspaceVisibility.PRIVATE)
    icon: Optional[str] = Field(default=None, description="Icon emoji or URL")
    color: Optional[str] = Field(default=None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color")
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a workspace."""
    organization_id: UUID = Field(description="Organization ID")
    parent_workspace_id: Optional[UUID] = Field(default=None, description="Parent workspace for hierarchy")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str], values: dict) -> Optional[str]:
        """Generate slug from name if not provided."""
        if not v and "name" in values:
            import re
            slug = re.sub(r'[^\w\s-]', '', values["name"].lower())
            slug = re.sub(r'[-\s]+', '-', slug).strip('-')
            return slug
        return v


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    type: Optional[WorkspaceType] = None
    visibility: Optional[WorkspaceVisibility] = None
    icon: Optional[str] = None
    color: Optional[str] = Field(default=None, pattern="^#[0-9A-Fa-f]{6}$")
    settings: Optional[Dict[str, Any]] = None
    is_archived: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceResponse(WorkspaceBase, TimestampMixin):
    """Workspace response schema."""
    id: UUID
    organization_id: UUID
    organization_name: str
    created_by_id: UUID
    created_by_name: str
    parent_workspace_id: Optional[UUID] = None
    is_archived: bool = False
    member_count: int = Field(default=0, description="Number of members")
    project_count: int = Field(default=0, description="Number of projects")
    agent_count: int = Field(default=0, description="Number of AI agents")
    settings: Dict[str, Any] = Field(default_factory=dict)
    current_user_role: Optional[MemberRole] = Field(default=None, description="Current user's role")
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceListResponse(PaginatedResponse[WorkspaceResponse]):
    """Paginated workspace list response."""
    pass


class WorkspaceMemberBase(BaseModel):
    """Base workspace member schema."""
    user_id: UUID = Field(description="User ID")
    role: MemberRole = Field(default=MemberRole.MEMBER, description="Member role")
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberCreate(WorkspaceMemberBase):
    """Schema for adding a workspace member."""
    send_invite: bool = Field(default=True, description="Send invitation email")
    message: Optional[str] = Field(default=None, max_length=500, description="Invitation message")


class WorkspaceMemberUpdate(BaseModel):
    """Schema for updating a workspace member."""
    role: Optional[MemberRole] = None
    permissions: Optional[List[str]] = None
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberResponse(WorkspaceMemberBase, TimestampMixin):
    """Workspace member response schema."""
    id: UUID
    workspace_id: UUID
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    last_active: Optional[datetime] = None
    invited_by_id: Optional[UUID] = None
    invited_by_name: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceStats(BaseModel):
    """Workspace statistics."""
    total_projects: int = Field(description="Total number of projects")
    active_projects: int = Field(description="Number of active projects")
    total_stories: int = Field(description="Total number of stories")
    completed_stories: int = Field(description="Number of completed stories")
    total_documents: int = Field(description="Total number of documents")
    total_agents: int = Field(description="Total number of AI agents")
    active_members: int = Field(description="Number of active members")
    storage_used_mb: float = Field(description="Storage used in MB")
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceActivity(BaseModel):
    """Workspace activity entry."""
    id: UUID
    workspace_id: UUID
    user_id: UUID
    user_name: str
    action: str = Field(description="Action performed")
    entity_type: str = Field(description="Type of entity affected")
    entity_id: Optional[UUID] = None
    entity_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)