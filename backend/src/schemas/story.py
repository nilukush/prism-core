"""
Story-related Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from backend.src.schemas.common import TimestampMixin, PaginatedResponse


class StoryStatus(str, Enum):
    """Story status enum."""
    DRAFT = "draft"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"


class StoryType(str, Enum):
    """Story type enum."""
    FEATURE = "feature"
    BUG = "bug"
    TECHNICAL = "technical"
    IMPROVEMENT = "improvement"
    RESEARCH = "research"


class StoryPriority(str, Enum):
    """Story priority enum."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StoryBase(BaseModel):
    """Base story schema."""
    title: str = Field(min_length=1, max_length=255, description="Story title")
    description: Optional[str] = Field(default=None, description="Story description")
    type: StoryType = Field(default=StoryType.FEATURE)
    status: StoryStatus = Field(default=StoryStatus.DRAFT)
    priority: StoryPriority = Field(default=StoryPriority.MEDIUM)
    points: Optional[int] = Field(default=None, ge=0, le=100, description="Story points")
    
    model_config = ConfigDict(from_attributes=True)


class StoryCreate(StoryBase):
    """Schema for creating a story."""
    project_id: UUID = Field(description="Project ID")
    epic_id: Optional[UUID] = Field(default=None, description="Epic ID")
    sprint_id: Optional[UUID] = Field(default=None, description="Sprint ID")
    assignee_id: Optional[UUID] = Field(default=None, description="Assignee user ID")
    labels: Optional[List[str]] = Field(default_factory=list, description="Story labels")
    acceptance_criteria: Optional[List[str]] = Field(default_factory=list)
    technical_notes: Optional[str] = Field(default=None)
    external_id: Optional[str] = Field(default=None, description="External system ID")


class StoryUpdate(BaseModel):
    """Schema for updating a story."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    type: Optional[StoryType] = None
    status: Optional[StoryStatus] = None
    priority: Optional[StoryPriority] = None
    points: Optional[int] = Field(default=None, ge=0, le=100)
    epic_id: Optional[UUID] = None
    sprint_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    labels: Optional[List[str]] = None
    acceptance_criteria: Optional[List[str]] = None
    technical_notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class StoryResponse(StoryBase, TimestampMixin):
    """Story response schema."""
    id: UUID
    project_id: UUID
    project_name: str
    epic_id: Optional[UUID] = None
    epic_name: Optional[str] = None
    sprint_id: Optional[UUID] = None
    sprint_name: Optional[str] = None
    created_by_id: UUID
    created_by_name: str
    assignee_id: Optional[UUID] = None
    assignee_name: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    technical_notes: Optional[str] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    comment_count: int = Field(default=0)
    attachment_count: int = Field(default=0)
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class StoryListResponse(PaginatedResponse[StoryResponse]):
    """Paginated story list response."""
    pass


class StoryComment(BaseModel):
    """Story comment schema."""
    id: UUID
    story_id: UUID
    user_id: UUID
    user_name: str
    user_avatar: Optional[str] = None
    content: str
    edited_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StoryCommentCreate(BaseModel):
    """Schema for creating a story comment."""
    content: str = Field(min_length=1, max_length=5000)


class StoryAttachment(BaseModel):
    """Story attachment schema."""
    id: UUID
    story_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    url: str
    uploaded_by_id: UUID
    uploaded_by_name: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StoryActivity(BaseModel):
    """Story activity/history entry."""
    id: UUID
    story_id: UUID
    user_id: UUID
    user_name: str
    action: str = Field(description="Action performed")
    changes: Optional[Dict[str, Any]] = Field(default=None, description="What changed")
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StoryBulkUpdate(BaseModel):
    """Schema for bulk updating stories."""
    story_ids: List[UUID] = Field(description="Stories to update")
    updates: StoryUpdate = Field(description="Updates to apply")
    
    
class StoryMetrics(BaseModel):
    """Story metrics."""
    total_stories: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    completed_this_sprint: int
    average_cycle_time_hours: Optional[float] = None
    average_story_points: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)