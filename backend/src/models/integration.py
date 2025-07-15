"""
Integration models for external services like Jira, Confluence, Slack, etc.
"""

from datetime import datetime
from typing import List, Optional, Any

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
import enum

from backend.src.models.base import Base, TimestampMixin, SoftDeleteMixin


class IntegrationType(str, enum.Enum):
    """Integration type."""
    JIRA = "jira"
    CONFLUENCE = "confluence"
    SLACK = "slack"
    TEAMS = "teams"
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class IntegrationStatus(str, enum.Enum):
    """Integration status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class Integration(Base, TimestampMixin, SoftDeleteMixin):
    """Integration configuration for external services."""
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[IntegrationType] = mapped_column(
        SQLEnum(IntegrationType),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[IntegrationStatus] = mapped_column(
        SQLEnum(IntegrationStatus),
        nullable=False,
        default=IntegrationStatus.PENDING
    )
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Configuration (encrypted in production)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Settings
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    
    # Foreign keys
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )
    created_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="integrations"
    )
    created_by: Mapped["User"] = relationship("User")
    configs: Mapped[List["IntegrationConfig"]] = relationship(
        "IntegrationConfig",
        back_populates="integration",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("organization_id", "type", "name", name="uq_org_integration"),
        Index("idx_integration_organization_type", "organization_id", "type"),
        Index("idx_integration_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Integration(id={self.id}, name={self.name}, type={self.type})>"
    
    @hybrid_property
    def is_active(self) -> bool:
        """Check if integration is active and enabled."""
        return self.is_enabled and self.status == IntegrationStatus.ACTIVE
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self.config.get(key, default)
    
    def set_config_value(self, key: str, value: Any) -> None:
        """Set configuration value."""
        if self.config is None:
            self.config = {}
        self.config[key] = value
    
    def mask_sensitive_config(self) -> dict:
        """Return config with sensitive values masked."""
        masked_config = self.config.copy()
        sensitive_keys = ["api_key", "api_token", "password", "secret", "token"]
        
        for key in masked_config:
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                if masked_config[key]:
                    masked_config[key] = "***" + str(masked_config[key])[-4:]
        
        return masked_config
    
    def to_dict_safe(self) -> dict:
        """Convert to dictionary with masked sensitive data."""
        data = self.to_dict()
        data["config"] = self.mask_sensitive_config()
        return data


class IntegrationConfig(Base, TimestampMixin):
    """Project-specific integration configuration."""
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign keys
    integration_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("integration.id", ondelete="CASCADE"),
        nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Configuration
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Sync settings
    sync_stories: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sync_documents: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sync_comments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Field mappings
    field_mappings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    integration: Mapped["Integration"] = relationship(
        "Integration",
        back_populates="configs"
    )
    project: Mapped["Project"] = relationship("Project")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("integration_id", "project_id", name="uq_integration_project"),
        Index("idx_integration_config", "integration_id", "project_id"),
    )
    
    def __repr__(self) -> str:
        return f"<IntegrationConfig(id={self.id}, integration_id={self.integration_id}, project_id={self.project_id})>"
    
    def get_mapped_field(self, prism_field: str) -> Optional[str]:
        """Get external field name for PRISM field."""
        return self.field_mappings.get(prism_field)
    
    def set_field_mapping(self, prism_field: str, external_field: str) -> None:
        """Set field mapping."""
        if self.field_mappings is None:
            self.field_mappings = {}
        self.field_mappings[prism_field] = external_field