"""
Workspace model and related database tables.
"""

from typing import TYPE_CHECKING, List, Optional
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Text, ForeignKey, Boolean, JSON, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from backend.src.models.base import Base, TimestampMixin
from backend.src.schemas.workspace import WorkspaceType, WorkspaceVisibility, MemberRole

if TYPE_CHECKING:
    from backend.src.models.user import User
    from backend.src.models.organization import Organization
    from backend.src.models.project import Project
    from backend.src.models.agent import Agent


class Workspace(Base, TimestampMixin):
    """
    Workspace model representing a collaborative space within an organization.
    Workspaces can be hierarchical and contain projects, documents, and AI agents.
    """
    __tablename__ = "workspaces"
    
    # Primary fields
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Type and visibility
    type: Mapped[WorkspaceType] = mapped_column(
        SQLEnum(WorkspaceType, native_enum=False),
        default=WorkspaceType.PROJECT,
        nullable=False
    )
    visibility: Mapped[WorkspaceVisibility] = mapped_column(
        SQLEnum(WorkspaceVisibility, native_enum=False),
        default=WorkspaceVisibility.PRIVATE,
        nullable=False
    )
    
    # Appearance
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color
    
    # Status
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Settings and metadata
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Foreign keys
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    parent_workspace_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="workspaces"
    )
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by_id]
    )
    parent_workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace",
        remote_side=[id],
        backref="child_workspaces"
    )
    
    # Collections
    members: Mapped[List["WorkspaceMember"]] = relationship(
        "WorkspaceMember",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    agents: Mapped[List["Agent"]] = relationship(
        "Agent",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_workspace_org_slug"),
        Index("idx_workspace_org_type", "organization_id", "type"),
        Index("idx_workspace_archived", "is_archived"),
    )
    
    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, name='{self.name}', org_id={self.organization_id})>"


class WorkspaceMember(Base, TimestampMixin):
    """
    Workspace member model representing a user's membership in a workspace.
    Tracks role, permissions, and invitation details.
    """
    __tablename__ = "workspace_members"
    
    # Primary fields
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    # Role and permissions
    role: Mapped[MemberRole] = mapped_column(
        SQLEnum(MemberRole, native_enum=False),
        default=MemberRole.MEMBER,
        nullable=False
    )
    permissions: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    
    # Activity tracking
    last_active: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Foreign keys
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    invited_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="members"
    )
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="workspace_memberships"
    )
    invited_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[invited_by_id]
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
        Index("idx_workspace_member_user", "user_id"),
        Index("idx_workspace_member_role", "workspace_id", "role"),
    )
    
    def __repr__(self) -> str:
        return f"<WorkspaceMember(workspace_id={self.workspace_id}, user_id={self.user_id}, role={self.role})>"