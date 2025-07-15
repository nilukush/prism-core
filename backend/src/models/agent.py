"""
AI Agent model and related database tables.
"""

from typing import TYPE_CHECKING, List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Text, ForeignKey, Boolean, JSON, Integer, Float, Enum as SQLEnum, UniqueConstraint, Index, Table, Column, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from backend.src.models.base import Base, TimestampMixin
from backend.src.schemas.agent import AgentType, AgentStatus, ExecutionStatus, AgentCapability

if TYPE_CHECKING:
    from backend.src.models.user import User
    from backend.src.models.workspace import Workspace
    from backend.src.models.document import Document


class Agent(Base, TimestampMixin):
    """
    AI Agent model representing an intelligent agent that can perform tasks.
    Agents are scoped to workspaces and can have multiple versions.
    """
    __tablename__ = "agents"
    
    # Primary fields
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Type and status
    type: Mapped[AgentType] = mapped_column(
        SQLEnum(AgentType, native_enum=False),
        nullable=False
    )
    status: Mapped[AgentStatus] = mapped_column(
        SQLEnum(AgentStatus, native_enum=False),
        default=AgentStatus.ACTIVE,
        nullable=False
    )
    
    # Model configuration
    model_provider: Mapped[str] = mapped_column(String(50), default="openai", nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), default="gpt-3.5-turbo", nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    
    # Capabilities and configuration
    capabilities: Mapped[List[AgentCapability]] = mapped_column(JSON, default=list, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    tools: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metrics
    execution_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Foreign keys
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="agents"
    )
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by_id]
    )
    
    # Collections
    versions: Mapped[List["AgentVersion"]] = relationship(
        "AgentVersion",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    executions: Mapped[List["AgentExecution"]] = relationship(
        "AgentExecution",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    knowledge_sources: Mapped[List["Document"]] = relationship(
        "Document",
        secondary="agent_knowledge_source",
        back_populates="agents"
    )
    
    # Table constraints
    __table_args__ = (
        Index("idx_agent_workspace_type", "workspace_id", "type"),
        Index("idx_agent_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name='{self.name}', type={self.type})>"


class AgentVersion(Base, TimestampMixin):
    """
    Agent version model for tracking changes to agent configuration.
    """
    __tablename__ = "agent_versions"
    
    # Primary fields
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Changes tracking
    changes: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Foreign keys
    agent_id: Mapped[UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="versions"
    )
    created_by: Mapped[Optional["User"]] = relationship("User")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint("agent_id", "version", name="uq_agent_version"),
        Index("idx_agent_version_active", "agent_id", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<AgentVersion(agent_id={self.agent_id}, version={self.version})>"


class AgentExecution(Base, TimestampMixin):
    """
    Agent execution model for tracking agent runs and results.
    """
    __tablename__ = "agent_executions"
    
    # Primary fields
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    # Execution details
    status: Mapped[ExecutionStatus] = mapped_column(
        SQLEnum(ExecutionStatus, native_enum=False),
        default=ExecutionStatus.PENDING,
        nullable=False
    )
    agent_version: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Input/Output
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Usage metrics
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float)
    
    # Foreign keys
    agent_id: Mapped[UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False
    )
    executed_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="executions"
    )
    executed_by: Mapped[Optional["User"]] = relationship("User")
    
    # Table constraints
    __table_args__ = (
        Index("idx_agent_execution_status", "agent_id", "status"),
        Index("idx_agent_execution_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<AgentExecution(id={self.id}, agent_id={self.agent_id}, status={self.status})>"


# Association table for agent knowledge sources
agent_knowledge_source = Table(
    "agent_knowledge_source",
    Base.metadata,
    Column("agent_id", ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)