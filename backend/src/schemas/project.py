"""
Project-related Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from backend.src.schemas.common import TimestampMixin, PaginatedResponse


class ProjectStatus(str, Enum):
    """Project status enum."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ProjectMethodology(str, Enum):
    """Project methodology."""
    AGILE = "agile"
    SCRUM = "scrum"
    KANBAN = "kanban"
    WATERFALL = "waterfall"
    HYBRID = "hybrid"


class SprintStatus(str, Enum):
    """Sprint status."""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(min_length=1, max_length=255, description="Project name")
    code: str = Field(min_length=2, max_length=20, pattern="^[A-Z][A-Z0-9]*$", description="Project code")
    description: Optional[str] = Field(default=None, max_length=2000)
    methodology: ProjectMethodology = Field(default=ProjectMethodology.AGILE)
    
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    workspace_id: UUID = Field(description="Workspace ID")
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    budget: Optional[float] = Field(default=None, ge=0)
    repository_url: Optional[str] = Field(default=None)
    documentation_url: Optional[str] = Field(default=None)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    methodology: Optional[ProjectMethodology] = None
    status: Optional[ProjectStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = Field(default=None, ge=0)
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(ProjectBase, TimestampMixin):
    """Project response schema."""
    id: UUID
    workspace_id: UUID
    workspace_name: str
    created_by_id: UUID
    created_by_name: str
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    budget: Optional[float] = None
    spent_budget: Optional[float] = None
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    team_size: int = Field(default=0)
    story_count: int = Field(default=0)
    completed_story_count: int = Field(default=0)
    epic_count: int = Field(default=0)
    sprint_count: int = Field(default=0)
    current_sprint_id: Optional[UUID] = None
    current_sprint_name: Optional[str] = None
    completion_percentage: float = Field(default=0.0)
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(PaginatedResponse[ProjectResponse]):
    """Paginated project list response."""
    pass


class ProjectMember(BaseModel):
    """Project team member."""
    id: UUID
    project_id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    user_avatar: Optional[str] = None
    role: str = Field(description="Role in project")
    allocation_percentage: int = Field(default=100, ge=0, le=100)
    joined_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProjectMemberAdd(BaseModel):
    """Schema for adding project member."""
    user_id: UUID
    role: str = Field(default="developer")
    allocation_percentage: int = Field(default=100, ge=0, le=100)


class EpicBase(BaseModel):
    """Base epic schema."""
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)
    
    model_config = ConfigDict(from_attributes=True)


class EpicCreate(EpicBase):
    """Schema for creating an epic."""
    project_id: UUID
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    color: Optional[str] = Field(default=None, pattern="^#[0-9A-Fa-f]{6}$")


class EpicResponse(EpicBase, TimestampMixin):
    """Epic response schema."""
    id: UUID
    project_id: UUID
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    color: Optional[str] = None
    story_count: int = Field(default=0)
    completed_story_count: int = Field(default=0)
    total_points: int = Field(default=0)
    completed_points: int = Field(default=0)
    
    model_config = ConfigDict(from_attributes=True)


class SprintBase(BaseModel):
    """Base sprint schema."""
    name: str = Field(min_length=1, max_length=255)
    goal: Optional[str] = Field(default=None, max_length=500)
    
    model_config = ConfigDict(from_attributes=True)


class SprintCreate(SprintBase):
    """Schema for creating a sprint."""
    project_id: UUID
    start_date: date
    end_date: date


class SprintUpdate(BaseModel):
    """Schema for updating a sprint."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    goal: Optional[str] = Field(default=None, max_length=500)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[SprintStatus] = None


class SprintResponse(SprintBase, TimestampMixin):
    """Sprint response schema."""
    id: UUID
    project_id: UUID
    number: int = Field(description="Sprint number")
    status: SprintStatus = SprintStatus.PLANNED
    start_date: date
    end_date: date
    story_count: int = Field(default=0)
    completed_story_count: int = Field(default=0)
    total_points: int = Field(default=0)
    completed_points: int = Field(default=0)
    velocity: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProjectStats(BaseModel):
    """Project statistics."""
    total_stories: int
    completed_stories: int
    in_progress_stories: int
    total_story_points: int
    completed_story_points: int
    average_cycle_time_days: Optional[float] = None
    velocity_per_sprint: Optional[float] = None
    team_size: int
    budget_utilization_percentage: Optional[float] = None
    days_remaining: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProjectRoadmap(BaseModel):
    """Project roadmap."""
    project_id: UUID
    epics: List[EpicResponse]
    sprints: List[SprintResponse]
    milestones: List[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)