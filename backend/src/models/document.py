"""
Document models for PRDs, technical specs, and other documentation.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from backend.src.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin


class DocumentType(str, enum.Enum):
    """Document type."""
    PRD = "prd"
    TECHNICAL_SPEC = "technical_spec"
    DESIGN_DOC = "design_doc"
    USER_GUIDE = "user_guide"
    API_DOC = "api_doc"
    MEETING_NOTES = "meeting_notes"
    RETROSPECTIVE = "retrospective"
    CUSTOM = "custom"


class DocumentStatus(str, enum.Enum):
    """Document status."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class Document(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Document model for various types of documentation."""
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType),
        nullable=False,
        default=DocumentType.CUSTOM
    )
    
    # Content
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.DRAFT
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Metadata
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    meta_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # AI generation metadata
    ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    generation_context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
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
    template_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("document_templates.id"),
        nullable=True
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("documents.id"),
        nullable=True
    )
    
    # External references
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[creator_id],
        back_populates="created_documents"
    )
    project: Mapped["Project"] = relationship("Project", back_populates="documents")
    template: Mapped[Optional["DocumentTemplate"]] = relationship(
        "DocumentTemplate",
        back_populates="documents"
    )
    parent: Mapped[Optional["Document"]] = relationship(
        "Document",
        remote_side=[id],
        backref="children"
    )
    versions: Mapped[List["DocumentVersion"]] = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    agents: Mapped[List["Agent"]] = relationship(
        "Agent",
        secondary="agent_knowledge_source",
        back_populates="knowledge_sources"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_document_project_type", "project_id", "type"),
        Index("idx_document_project_status", "project_id", "status"),
        Index("idx_document_slug", "slug"),
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title}, type={self.type})>"
    
    def create_version(self) -> "DocumentVersion":
        """Create a new version of the document."""
        version = DocumentVersion(
            document_id=self.id,
            version_number=self.version,
            title=self.title,
            content=self.content,
            raw_content=self.raw_content,
            created_by_id=self.updated_by_id or self.creator_id,
        )
        self.version += 1
        return version
    
    def to_confluence_format(self) -> dict:
        """Convert document to Confluence page format."""
        return {
            "title": self.title,
            "type": "page",
            "body": {
                "storage": {
                    "value": self.raw_content or "",
                    "representation": "storage"
                }
            },
            "metadata": {
                "labels": [{"name": tag} for tag in self.tags]
            }
        }


class DocumentVersion(Base, TimestampMixin):
    """Version history for documents."""
    __tablename__ = "document_versions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Version info
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Content snapshot
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Change info
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="versions")
    created_by: Mapped["User"] = relationship("User")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_document_version"),
        Index("idx_document_version", "document_id", "version_number"),
    )
    
    def __repr__(self) -> str:
        return f"<DocumentVersion(id={self.id}, document_id={self.document_id}, version={self.version_number})>"


class DocumentTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """Templates for document creation."""
    __tablename__ = "document_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType),
        nullable=False
    )
    
    # Template content
    structure: Mapped[dict] = mapped_column(JSON, nullable=False)
    example_content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    prompts: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Settings
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
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
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="template"
    )
    
    def __repr__(self) -> str:
        return f"<DocumentTemplate(id={self.id}, name={self.name}, type={self.type})>"