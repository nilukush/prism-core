"""
Project, sprint, and epic models for agile project management.
"""

from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from backend.src.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin


class ProjectStatus(str, enum.Enum):
    """Project status."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class SprintStatus(str, enum.Enum):
    """Sprint status."""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Project model for organizing work."""
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g., "PRISM"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus),
        nullable=False,
        default=ProjectStatus.PLANNING
    )
    
    # Dates
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Settings
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    default_story_points: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: [1, 2, 3, 5, 8, 13, 21]
    )
    
    # Foreign keys
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )
    workspace_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=True
    )
    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    
    # External references
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="projects"
    )
    workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace",
        back_populates="projects"
    )
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    sprints: Mapped[List["Sprint"]] = relationship(
        "Sprint",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    epics: Mapped[List["Epic"]] = relationship(
        "Epic",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    stories: Mapped[List["Story"]] = relationship(
        "Story",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("organization_id", "key", name="uq_org_project_key"),
        Index("idx_project_organization_status", "organization_id", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, key={self.key})>"
    
    def get_active_sprint(self) -> Optional["Sprint"]:
        """Get the currently active sprint."""
        for sprint in self.sprints:
            if sprint.status == SprintStatus.ACTIVE:
                return sprint
        return None
    
    def get_backlog_stories(self) -> List["Story"]:
        """Get stories not assigned to any sprint."""
        return [story for story in self.stories if story.sprint_id is None]
    
    def generate_story_id(self) -> str:
        """Generate next story ID."""
        count = len(self.stories) + 1
        return f"{self.key}-{count}"


class Sprint(Base, TimestampMixin, SoftDeleteMixin):
    """Sprint model for agile iterations."""
    __tablename__ = "sprints"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[SprintStatus] = mapped_column(
        SQLEnum(SprintStatus),
        nullable=False,
        default=SprintStatus.PLANNED
    )
    
    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Capacity
    capacity_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    capacity_hours: Mapped[Optional[float]] = mapped_column(Integer, nullable=True)
    
    # Foreign keys
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="sprints")
    stories: Mapped[List["Story"]] = relationship(
        "Story",
        back_populates="sprint"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_sprint_project_status", "project_id", "status"),
        Index("idx_sprint_dates", "start_date", "end_date"),
    )
    
    def __repr__(self) -> str:
        return f"<Sprint(id={self.id}, name={self.name}, status={self.status})>"
    
    def get_total_points(self) -> int:
        """Get total story points in sprint."""
        return sum(story.story_points or 0 for story in self.stories)
    
    def get_completed_points(self) -> int:
        """Get completed story points in sprint."""
        return sum(
            story.story_points or 0
            for story in self.stories
            if story.is_completed()
        )
    
    def get_velocity(self) -> float:
        """Get sprint velocity (completed points per day)."""
        if self.status != SprintStatus.COMPLETED:
            return 0.0
        days = (self.end_date - self.start_date).days
        if days == 0:
            return 0.0
        return self.get_completed_points() / days
    
    def can_add_story(self, story_points: int) -> bool:
        """Check if sprint has capacity for more stories."""
        if not self.capacity_points:
            return True
        current_points = self.get_total_points()
        return current_points + story_points <= self.capacity_points


class Epic(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Epic model for grouping related stories."""
    __tablename__ = "epics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Dates
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Color for UI
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6B46C1")
    
    # Foreign keys
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="epics")
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    stories: Mapped[List["Story"]] = relationship(
        "Story",
        back_populates="epic"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_epic_project", "project_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Epic(id={self.id}, name={self.name})>"
    
    def get_progress(self) -> float:
        """Get epic completion progress as percentage."""
        total_stories = len(self.stories)
        if total_stories == 0:
            return 0.0
        completed_stories = sum(1 for story in self.stories if story.is_completed())
        return (completed_stories / total_stories) * 100