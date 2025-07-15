"""
Prompt template-related Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator

from backend.src.schemas.common import TimestampMixin, PaginatedResponse


class PromptCategory(str, Enum):
    """Prompt template category."""
    STORY_WRITING = "story_writing"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    TEST_GENERATION = "test_generation"
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"
    SPRINT_PLANNING = "sprint_planning"
    DATA_ANALYSIS = "data_analysis"
    GENERAL = "general"
    CUSTOM = "custom"


class PromptTemplateBase(BaseModel):
    """Base prompt template schema."""
    name: str = Field(min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(default=None, max_length=1000)
    category: PromptCategory = Field(default=PromptCategory.GENERAL)
    content: str = Field(min_length=1, description="Template content with variables")
    
    model_config = ConfigDict(from_attributes=True)


class PromptTemplateCreate(PromptTemplateBase):
    """Schema for creating a prompt template."""
    variables: List[str] = Field(default_factory=list, description="Template variables")
    examples: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Usage examples")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for search")
    is_public: bool = Field(default=False, description="Whether template is public")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator("variables")
    @classmethod
    def extract_variables(cls, v: List[str], values: dict) -> List[str]:
        """Extract variables from content if not provided."""
        if not v and "content" in values:
            import re
            # Find all {{variable}} patterns
            matches = re.findall(r'\{\{(\w+)\}\}', values["content"])
            return list(set(matches))
        return v


class PromptTemplateUpdate(BaseModel):
    """Schema for updating a prompt template."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    category: Optional[PromptCategory] = None
    content: Optional[str] = Field(default=None, min_length=1)
    variables: Optional[List[str]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class PromptTemplateResponse(PromptTemplateBase, TimestampMixin):
    """Prompt template response schema."""
    id: UUID
    created_by_id: UUID
    created_by_name: str
    workspace_id: Optional[UUID] = None
    workspace_name: Optional[str] = None
    variables: List[str] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False
    usage_count: int = Field(default=0, description="Number of times used")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="Average rating")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class PromptTemplateListResponse(PaginatedResponse[PromptTemplateResponse]):
    """Paginated prompt template list response."""
    pass


class PromptExecutionRequest(BaseModel):
    """Request to execute a prompt template."""
    template_id: UUID = Field(description="Template ID to execute")
    variables: Dict[str, Any] = Field(description="Variable values")
    model_provider: Optional[str] = Field(default="openai", description="LLM provider")
    model_name: Optional[str] = Field(default="gpt-3.5-turbo", description="Model to use")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=2000, ge=1, le=32000)
    stream: bool = Field(default=False, description="Stream response")


class PromptExecutionResponse(BaseModel):
    """Prompt execution response."""
    id: UUID
    template_id: UUID
    template_name: str
    rendered_prompt: str = Field(description="Prompt with variables replaced")
    response: str = Field(description="LLM response")
    model_provider: str
    model_name: str
    tokens_used: int
    duration_ms: int
    cost_usd: Optional[float] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PromptTemplateVersion(BaseModel):
    """Prompt template version."""
    id: UUID
    template_id: UUID
    version: int
    content: str
    variables: List[str]
    changes: Optional[str] = Field(default=None, description="What changed")
    created_by_id: UUID
    created_by_name: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PromptTemplateRating(BaseModel):
    """Prompt template rating."""
    template_id: UUID
    user_id: UUID
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PromptLibraryFilter(BaseModel):
    """Filters for prompt library search."""
    category: Optional[PromptCategory] = None
    tags: Optional[List[str]] = None
    created_by: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    is_public: Optional[bool] = None
    min_rating: Optional[float] = Field(default=None, ge=0, le=5)
    search: Optional[str] = Field(default=None, description="Search in name and description")