"""
AI context models for managing prompts, conversations, and generated content.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index, JSON, Enum as SQLEnum, Float
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from backend.src.models.base import Base, TimestampMixin, SoftDeleteMixin


class ContextType(str, enum.Enum):
    """AI context type."""
    STORY_GENERATION = "story_generation"
    DOCUMENT_GENERATION = "document_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    CHAT = "chat"
    CUSTOM = "custom"


class ContentStatus(str, enum.Enum):
    """Generated content status."""
    DRAFT = "draft"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


class AIContext(Base, TimestampMixin, SoftDeleteMixin):
    """AI conversation context and memory."""
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Context info
    context_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    context_type: Mapped[ContextType] = mapped_column(
        SQLEnum(ContextType),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Context data
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Settings
    model_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="openai")
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="gpt-3.5-turbo")
    temperature: Mapped[Float] = mapped_column(Float, nullable=False, default=0.7)
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Usage tracking
    total_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
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
    conversations: Mapped[List["ConversationHistory"]] = relationship(
        "ConversationHistory",
        back_populates="context",
        cascade="all, delete-orphan"
    )
    generated_contents: Mapped[List["GeneratedContent"]] = relationship(
        "GeneratedContent",
        back_populates="context",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<AIContext(id={self.id}, context_id={self.context_id}, type={self.context_type})>"


class ConversationHistory(Base, TimestampMixin):
    """AI conversation history."""
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Message info
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Additional data
    meta_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Foreign keys
    context_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("aicontext.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    context: Mapped["AIContext"] = relationship("AIContext", back_populates="conversations")
    
    # Indexes
    __table_args__ = (
        Index("idx_conversation_context_timestamp", "context_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<ConversationHistory(id={self.id}, role={self.role}, context_id={self.context_id})>"


class PromptTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """Reusable prompt templates."""
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Template info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Template content
    template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # List of variable names
    examples: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Settings
    recommended_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recommended_temperature: Mapped[Optional[Float]] = mapped_column(Float, nullable=True)
    
    # Metadata
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Foreign keys
    created_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=True
    )
    
    # Relationships
    created_by: Mapped["User"] = relationship("User")
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    
    def __repr__(self) -> str:
        return f"<PromptTemplate(id={self.id}, name={self.name}, category={self.category})>"


class GeneratedContent(Base, TimestampMixin, SoftDeleteMixin):
    """AI-generated content tracking."""
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Content info
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Generated content
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Generation metadata
    model_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    temperature: Mapped[Float] = mapped_column(Float, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Status and review
    status: Mapped[ContentStatus] = mapped_column(
        SQLEnum(ContentStatus),
        nullable=False,
        default=ContentStatus.DRAFT
    )
    confidence_score: Mapped[Optional[Float]] = mapped_column(Float, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Application tracking
    applied_to_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    applied_to_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Foreign keys
    context_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("aicontext.id"),
        nullable=True,
        index=True
    )
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
    template_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("prompttemplate.id"),
        nullable=True
    )
    
    # Relationships
    context: Mapped[Optional["AIContext"]] = relationship("AIContext", back_populates="generated_contents")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    reviewed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by_id])
    project: Mapped[Optional["Project"]] = relationship("Project")
    template: Mapped[Optional["PromptTemplate"]] = relationship("PromptTemplate")
    
    # Indexes
    __table_args__ = (
        Index("idx_generated_content_status", "status"),
        Index("idx_generated_content_applied", "applied_to_type", "applied_to_id"),
    )
    
    def __repr__(self) -> str:
        return f"<GeneratedContent(id={self.id}, type={self.content_type}, status={self.status})>"