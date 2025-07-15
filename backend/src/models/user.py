"""
User, Role, and Permission models.
Handles authentication and authorization.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text,
    UniqueConstraint, Index, JSON, Enum as SQLEnum, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from backend.src.models.base import Base, TimestampMixin, SoftDeleteMixin


class UserStatus(str, enum.Enum):
    """User account status."""
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    pending = "pending"


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    "user_role",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


class User(Base, TimestampMixin, SoftDeleteMixin):
    """User model for authentication and profile."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    
    # Status
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, name='user_status', native_enum=True),
        nullable=False,
        default=UserStatus.pending
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Security
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Preferences
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    owned_organizations: Mapped[List["Organization"]] = relationship(
        "Organization",
        back_populates="owner",
        foreign_keys="Organization.owner_id"
    )
    organizations: Mapped[List["Organization"]] = relationship(
        "Organization",
        secondary="organization_members",
        back_populates="members"
    )
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users"
    )
    created_stories: Mapped[List["Story"]] = relationship(
        "Story",
        back_populates="creator",
        foreign_keys="Story.creator_id"
    )
    created_documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="creator",
        foreign_keys="Document.creator_id"
    )
    workspace_memberships: Mapped[List["WorkspaceMember"]] = relationship(
        "WorkspaceMember",
        back_populates="user",
        foreign_keys="WorkspaceMember.user_id"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_user_email_status", "email", "status"),
        Index("idx_user_username_status", "username", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
    
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.active and not self.is_deleted
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    def get_permissions(self) -> set[str]:
        """Get all user permissions."""
        permissions = set()
        for role in self.roles:
            for permission in role.permissions:
                permissions.add(permission.name)
        return permissions
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission."""
        return permission_name in self.get_permissions()


class Role(Base, TimestampMixin):
    """Role model for RBAC."""
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Relationships
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base, TimestampMixin):
    """Permission model for RBAC."""
    __tablename__ = "permissions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )
    
    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name={self.name})>"