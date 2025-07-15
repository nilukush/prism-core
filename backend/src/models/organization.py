"""
Organization and team models.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from backend.src.models.base import Base, TimestampMixin, SoftDeleteMixin


class OrganizationPlan(str, enum.Enum):
    """Organization subscription plan."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Organization(Base, TimestampMixin, SoftDeleteMixin):
    """Organization model."""
    __tablename__ = "organizations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Contact info
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Plan and limits
    plan: Mapped[OrganizationPlan] = mapped_column(
        SQLEnum(OrganizationPlan),
        nullable=False,
        default=OrganizationPlan.FREE
    )
    max_users: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    max_projects: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    max_storage_gb: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    
    # Settings
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Billing
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Foreign keys
    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_organizations")
    members: Mapped[List["User"]] = relationship(
        "User",
        secondary="organization_members",
        back_populates="organizations"
    )
    teams: Mapped[List["Team"]] = relationship(
        "Team",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    workspaces: Mapped[List["Workspace"]] = relationship(
        "Workspace",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    integrations: Mapped[List["Integration"]] = relationship(
        "Integration",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, slug={self.slug})>"


class OrganizationMember(Base):
    """Organization membership association table."""
    __tablename__ = "organization_members"
    
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        primary_key=True
    )
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        primary_key=True
    )
    
    # Member info
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()"
    )
    
    # Constraints
    __table_args__ = (
        Index("idx_org_member", "organization_id", "user_id"),
    )


class Team(Base, TimestampMixin, SoftDeleteMixin):
    """Team within an organization."""
    __tablename__ = "teams"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Settings
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Foreign keys
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="teams")
    members: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan"
    )
    # projects: Mapped[List["Project"]] = relationship(
    #     "Project",
    #     secondary="project_team",
    #     back_populates="teams"
    # )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_org_team_slug"),
        Index("idx_team_organization", "organization_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name={self.name}, org_id={self.organization_id})>"


class TeamMember(Base, TimestampMixin):
    """Team membership."""
    __tablename__ = "team_members"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign keys
    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Member info
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    
    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship("User")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_member"),
        Index("idx_team_member", "team_id", "user_id"),
    )
    
    def __repr__(self) -> str:
        return f"<TeamMember(id={self.id}, team_id={self.team_id}, user_id={self.user_id})>"


# class ProjectTeam(Base):
#     """Project-team association table."""
#     
#     project_id: Mapped[int] = mapped_column(
#         Integer,
#         ForeignKey("projects.id"),
#         primary_key=True
#     )
#     team_id: Mapped[int] = mapped_column(
#         Integer,
#         ForeignKey("teams.id"),
#         primary_key=True
#     )
#     
#     # Access level
#     access_level: Mapped[str] = mapped_column(
#         String(50),
#         nullable=False,
#         default="read"
#     )
#     
#     # Constraints
#     __table_args__ = (
#         Index("idx_project_team", "project_id", "team_id"),
#     )