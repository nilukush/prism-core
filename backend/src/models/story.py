"""
User story models.
Handles agile user stories with acceptance criteria.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index, JSON, Enum as SQLEnum, Float
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from backend.src.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin


class StoryStatus(str, enum.Enum):
    """Story status."""
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    ARCHIVED = "archived"


class StoryPriority(str, enum.Enum):
    """Story priority."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Story(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """User story model."""
    __tablename__ = "stories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    story_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Story components
    user_type: Mapped[str] = mapped_column(String(100), nullable=False)  # As a...
    user_story: Mapped[str] = mapped_column(Text, nullable=False)  # I want...
    benefit: Mapped[str] = mapped_column(Text, nullable=False)  # So that...
    
    # Details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    technical_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Estimation
    story_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_estimate_hours: Mapped[Optional[Float]] = mapped_column(Float, nullable=True)
    
    # Status and priority
    status: Mapped[StoryStatus] = mapped_column(
        SQLEnum(StoryStatus),
        nullable=False,
        default=StoryStatus.DRAFT
    )
    priority: Mapped[StoryPriority] = mapped_column(
        SQLEnum(StoryPriority),
        nullable=False,
        default=StoryPriority.MEDIUM
    )
    
    # Metadata  
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    labels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # AI generation metadata
    ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_confidence_score: Mapped[Optional[Float]] = mapped_column(Float, nullable=True)
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    creator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )
    epic_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("epics.id"),
        nullable=True
    )
    sprint_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sprints.id"),
        nullable=True
    )
    assignee_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )
    
    # External references
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Jira ID, etc.
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[creator_id],
        back_populates="created_stories"
    )
    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assignee_id]
    )
    project: Mapped["Project"] = relationship("Project", back_populates="stories")
    epic: Mapped[Optional["Epic"]] = relationship("Epic", back_populates="stories")
    sprint: Mapped[Optional["Sprint"]] = relationship("Sprint", back_populates="stories")
    comments: Mapped[List["StoryComment"]] = relationship(
        "StoryComment",
        back_populates="story",
        cascade="all, delete-orphan"
    )
    attachments: Mapped[List["StoryAttachment"]] = relationship(
        "StoryAttachment",
        back_populates="story",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_story_project_status", "project_id", "status"),
        Index("idx_story_sprint_status", "sprint_id", "status"),
        Index("idx_story_assignee_status", "assignee_id", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Story(id={self.id}, story_id={self.story_id}, title={self.title})>"
    
    @property
    def formatted_story(self) -> str:
        """Get formatted user story."""
        return f"As a {self.user_type}, I want {self.user_story} so that {self.benefit}"
    
    def is_completed(self) -> bool:
        """Check if story is completed."""
        return self.status == StoryStatus.DONE
    
    def can_start(self) -> bool:
        """Check if story can be started."""
        return self.status == StoryStatus.READY
    
    def to_jira_format(self) -> dict:
        """Convert story to Jira issue format."""
        return {
            "summary": self.title,
            "description": self.formatted_story + "\n\n" + (self.description or ""),
            "issuetype": {"name": "Story"},
            "priority": {"name": self.priority.value.capitalize()},
            "labels": self.labels,
            "customfield_10000": self.story_points,  # Story points field
        }


class StoryComment(Base, TimestampMixin, SoftDeleteMixin):
    """Comment on a story."""
    __tablename__ = "story_comments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Foreign keys
    story_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="comments")
    author: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<StoryComment(id={self.id}, story_id={self.story_id})>"


class StoryAttachment(Base, TimestampMixin):
    """Attachment for a story."""
    __tablename__ = "story_attachments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # File info
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Foreign keys
    story_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False
    )
    uploaded_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="attachments")
    uploaded_by: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<StoryAttachment(id={self.id}, filename={self.filename})>"