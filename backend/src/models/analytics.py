"""
Analytics models for tracking usage and metrics.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index, JSON, Enum as SQLEnum, Float
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from backend.src.models.base import Base, TimestampMixin


class EventType(str, enum.Enum):
    """Analytics event type."""
    PAGE_VIEW = "page_view"
    FEATURE_USE = "feature_use"
    API_CALL = "api_call"
    ERROR = "error"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"


class AnalyticsEvent(Base, TimestampMixin):
    """Analytics event tracking."""
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Event info
    event_type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType),
        nullable=False,
        index=True
    )
    event_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Event data
    properties: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Context
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Foreign keys
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=True,
        index=True
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True,
        index=True
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    project: Mapped[Optional["Project"]] = relationship("Project")
    
    # Indexes
    __table_args__ = (
        Index("idx_analytics_event_timestamp", "created_at"),
        Index("idx_analytics_event_user_timestamp", "user_id", "created_at"),
        Index("idx_analytics_event_org_timestamp", "organization_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<AnalyticsEvent(id={self.id}, type={self.event_type}, name={self.event_name})>"


class UserActivity(Base, TimestampMixin):
    """User activity tracking."""
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Activity info
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    activity_description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Resource info
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Additional data
    meta_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True,
        index=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    project: Mapped[Optional["Project"]] = relationship("Project")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_activity_timestamp", "created_at"),
        Index("idx_user_activity_user_timestamp", "user_id", "created_at"),
        Index("idx_user_activity_resource", "resource_type", "resource_id"),
    )
    
    def __repr__(self) -> str:
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type={self.activity_type})>"


class ProjectMetrics(Base, TimestampMixin):
    """Project-level metrics and statistics."""
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Metrics date
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    # Story metrics
    total_stories: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_stories: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    in_progress_stories: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    story_points_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Document metrics
    total_documents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    documents_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    documents_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Team metrics
    active_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # AI metrics
    ai_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Custom metrics
    custom_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Foreign keys
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )
    
    # Relationships
    project: Mapped["Project"] = relationship("Project")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("project_id", "date", name="uq_project_metrics_date"),
        Index("idx_project_metrics_date", "project_id", "date"),
    )
    
    def __repr__(self) -> str:
        return f"<ProjectMetrics(id={self.id}, project_id={self.project_id}, date={self.date})>"


class AIUsageMetrics(Base, TimestampMixin):
    """AI usage tracking and metrics."""
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Request info
    model_provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # generation, embedding, etc.
    
    # Usage metrics
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Performance metrics
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Cost tracking
    estimated_cost: Mapped[Optional[Float]] = mapped_column(Float, nullable=True)
    
    # Context
    context_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    context_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    organization: Mapped["Organization"] = relationship("Organization")
    project: Mapped[Optional["Project"]] = relationship("Project")
    
    # Indexes
    __table_args__ = (
        Index("idx_ai_usage_timestamp", "created_at"),
        Index("idx_ai_usage_org_timestamp", "organization_id", "created_at"),
        Index("idx_ai_usage_model", "model_provider", "model_name"),
    )
    
    def __repr__(self) -> str:
        return f"<AIUsageMetrics(id={self.id}, model={self.model_name}, tokens={self.total_tokens})>"