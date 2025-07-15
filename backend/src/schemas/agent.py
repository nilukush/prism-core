"""
AI Agent-related Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator

from backend.src.schemas.common import TimestampMixin, PaginatedResponse, SortDirection


class AgentType(str, Enum):
    """Agent type enum."""
    STORY_WRITER = "story_writer"
    REQUIREMENT_ANALYST = "requirement_analyst"
    TEST_GENERATOR = "test_generator"
    DOCUMENTATION = "documentation"
    CODE_REVIEWER = "code_reviewer"
    SPRINT_PLANNER = "sprint_planner"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    """Agent status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    ERROR = "error"
    DEPRECATED = "deprecated"


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class AgentCapability(str, Enum):
    """Agent capabilities."""
    STORY_GENERATION = "story_generation"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    TEST_CASE_GENERATION = "test_case_generation"
    DOCUMENTATION_GENERATION = "documentation_generation"
    CODE_REVIEW = "code_review"
    SPRINT_PLANNING = "sprint_planning"
    DATA_ANALYSIS = "data_analysis"
    NATURAL_LANGUAGE_QUERY = "natural_language_query"


class AgentBase(BaseModel):
    """Base agent schema."""
    name: str = Field(min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(default=None, max_length=1000)
    type: AgentType = Field(description="Agent type")
    model_provider: str = Field(default="openai", description="LLM provider")
    model_name: str = Field(default="gpt-3.5-turbo", description="Model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=2000, ge=1, le=32000, description="Max tokens")
    capabilities: List[AgentCapability] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class AgentCreate(AgentBase):
    """Schema for creating an agent."""
    workspace_id: UUID = Field(description="Workspace ID")
    system_prompt: Optional[str] = Field(default=None, description="System prompt")
    instructions: Optional[str] = Field(default=None, description="Agent instructions")
    tools: Optional[List[str]] = Field(default_factory=list, description="Available tools")
    knowledge_sources: Optional[List[UUID]] = Field(default_factory=list, description="Document IDs for context")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")
    is_public: bool = Field(default=False, description="Whether agent is public")


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=32000)
    system_prompt: Optional[str] = None
    instructions: Optional[str] = None
    tools: Optional[List[str]] = None
    knowledge_sources: Optional[List[UUID]] = None
    parameters: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[AgentCapability]] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)


class AgentResponse(AgentBase, TimestampMixin):
    """Agent response schema."""
    id: UUID
    workspace_id: UUID
    workspace_name: str
    created_by_id: UUID
    created_by_name: str
    status: AgentStatus = AgentStatus.ACTIVE
    is_active: bool = True
    is_public: bool = False
    version: int = Field(description="Current version number")
    system_prompt: Optional[str] = None
    instructions: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    knowledge_sources: List[UUID] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    execution_count: int = Field(default=0, description="Number of executions")
    success_rate: float = Field(default=0.0, description="Success rate percentage")
    average_duration_ms: int = Field(default=0, description="Average execution duration")
    last_executed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(PaginatedResponse[AgentResponse]):
    """Paginated agent list response."""
    pass


class AgentVersionResponse(TimestampMixin):
    """Agent version response."""
    id: UUID
    agent_id: UUID
    version: int
    created_by_id: UUID
    created_by_name: str
    changes: Dict[str, Any] = Field(description="What changed in this version")
    is_active: bool = Field(description="Whether this is the active version")
    
    model_config = ConfigDict(from_attributes=True)


class AgentExecutionCreate(BaseModel):
    """Schema for creating an agent execution."""
    input_data: Dict[str, Any] = Field(description="Input data for execution")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Override parameters")
    timeout_seconds: Optional[int] = Field(default=300, ge=1, le=3600, description="Execution timeout")
    priority: Optional[int] = Field(default=5, ge=1, le=10, description="Execution priority")


class AgentExecutionResponse(TimestampMixin):
    """Agent execution response."""
    id: UUID
    agent_id: UUID
    agent_name: str
    agent_version: int
    status: ExecutionStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class AgentExecutionListResponse(PaginatedResponse[AgentExecutionResponse]):
    """Paginated agent execution list response."""
    pass


class AgentPromptTemplate(BaseModel):
    """Agent prompt template."""
    id: UUID
    name: str
    description: Optional[str] = None
    content: str = Field(description="Template content with variables")
    variables: List[str] = Field(default_factory=list, description="Required variables")
    category: str = Field(description="Template category")
    agent_type: Optional[AgentType] = None
    is_public: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class AgentMetrics(BaseModel):
    """Agent performance metrics."""
    agent_id: UUID
    period: str = Field(description="Time period (day, week, month)")
    execution_count: int
    success_count: int
    failure_count: int
    success_rate: float
    average_duration_ms: int
    median_duration_ms: int
    total_tokens_used: int
    total_cost_usd: float
    unique_users: int
    error_rate: float
    timeout_rate: float
    
    model_config = ConfigDict(from_attributes=True)