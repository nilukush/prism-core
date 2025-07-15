"""
Document-related Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, HttpUrl

from backend.src.schemas.common import TimestampMixin, PaginatedResponse


class DocumentType(str, Enum):
    """Document type enum."""
    REQUIREMENT = "requirement"
    DESIGN = "design"
    TECHNICAL = "technical"
    USER_GUIDE = "user_guide"
    API_DOCS = "api_docs"
    MEETING_NOTES = "meeting_notes"
    RESEARCH = "research"
    TEMPLATE = "template"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Document status."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DocumentFormat(str, Enum):
    """Document format."""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    PLAIN_TEXT = "plain_text"


class DocumentBase(BaseModel):
    """Base document schema."""
    title: str = Field(min_length=1, max_length=255, description="Document title")
    description: Optional[str] = Field(default=None, max_length=1000)
    type: DocumentType = Field(default=DocumentType.REQUIREMENT)
    format: DocumentFormat = Field(default=DocumentFormat.MARKDOWN)
    
    model_config = ConfigDict(from_attributes=True)


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    workspace_id: UUID = Field(description="Workspace ID")
    project_id: Optional[UUID] = Field(default=None, description="Project ID")
    parent_id: Optional[UUID] = Field(default=None, description="Parent document ID")
    content: Optional[str] = Field(default="", description="Document content")
    tags: Optional[List[str]] = Field(default_factory=list)
    is_template: bool = Field(default=False, description="Is this a template?")
    template_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    type: Optional[DocumentType] = None
    format: Optional[DocumentFormat] = None
    content: Optional[str] = None
    status: Optional[DocumentStatus] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(DocumentBase, TimestampMixin):
    """Document response schema."""
    id: UUID
    workspace_id: UUID
    workspace_name: str
    project_id: Optional[UUID] = None
    project_name: Optional[str] = None
    parent_id: Optional[UUID] = None
    created_by_id: UUID
    created_by_name: str
    last_modified_by_id: Optional[UUID] = None
    last_modified_by_name: Optional[str] = None
    status: DocumentStatus = DocumentStatus.DRAFT
    version: int = Field(default=1, description="Document version")
    content: Optional[str] = None
    word_count: int = Field(default=0)
    tags: List[str] = Field(default_factory=list)
    is_template: bool = False
    template_variables: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    view_count: int = Field(default=0)
    edit_count: int = Field(default=0)
    share_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(PaginatedResponse[DocumentResponse]):
    """Paginated document list response."""
    pass


class DocumentVersion(BaseModel):
    """Document version schema."""
    id: UUID
    document_id: UUID
    version: int
    title: str
    content: str
    created_by_id: UUID
    created_by_name: str
    change_summary: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DocumentVersionListResponse(PaginatedResponse[DocumentVersion]):
    """Paginated document version list response."""
    pass


class DocumentUploadRequest(BaseModel):
    """Document upload request schema."""
    workspace_id: UUID
    project_id: Optional[UUID] = None
    title: Optional[str] = Field(default=None, description="Override filename as title")
    description: Optional[str] = None
    type: DocumentType = DocumentType.OTHER
    tags: Optional[List[str]] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    """Document upload response schema."""
    document_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    format: DocumentFormat
    status: str = "processing"
    message: str
    
    model_config = ConfigDict(from_attributes=True)


class DocumentExportRequest(BaseModel):
    """Document export request schema."""
    format: DocumentFormat = Field(description="Export format")
    include_metadata: bool = Field(default=True)
    include_comments: bool = Field(default=False)
    include_history: bool = Field(default=False)


class DocumentShareRequest(BaseModel):
    """Document share request schema."""
    permission: str = Field(default="view", pattern="^(view|comment|edit)$")
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)
    password: Optional[str] = Field(default=None, min_length=8)


class DocumentShareResponse(BaseModel):
    """Document share response schema."""
    share_url: str
    share_id: UUID
    permission: str
    expires_at: Optional[datetime] = None
    password_protected: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class DocumentSearchRequest(BaseModel):
    """Document search request schema."""
    query: str = Field(min_length=1, max_length=500)
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    types: Optional[List[DocumentType]] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(default=20, ge=1, le=100)


class DocumentSearchResult(BaseModel):
    """Document search result."""
    document_id: UUID
    title: str
    description: Optional[str] = None
    type: DocumentType
    snippet: str = Field(description="Relevant text snippet")
    score: float = Field(description="Search relevance score")
    workspace_name: str
    project_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DocumentSearchResponse(BaseModel):
    """Document search response."""
    query: str
    total: int
    results: List[DocumentSearchResult]
    
    model_config = ConfigDict(from_attributes=True)