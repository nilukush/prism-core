"""
Pydantic schemas for request/response validation.
"""

# Common schemas
from backend.src.schemas.common import (
    SortDirection,
    TimestampMixin,
    PaginationParams,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
    HealthResponse,
)

# Auth schemas
from backend.src.schemas.auth import (
    Token,
    TokenPayload,
    UserLogin,
    UserRegister,
    PasswordReset,
    PasswordResetConfirm,
    RefreshTokenRequest,
    EmailVerification,
    PasswordChange,
)

# User schemas
from backend.src.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserProfile,
    UserProfileUpdate,
    UserRole,
    UserStatus,
)

# Organization schemas
from backend.src.schemas.organization import (
    OrganizationBase,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationStats,
    OrganizationMember,
    OrganizationInvite,
    OrganizationPlan,
    OrganizationStatus,
)

# Workspace schemas
from backend.src.schemas.workspace import (
    WorkspaceBase,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse,
    WorkspaceMemberCreate,
    WorkspaceMemberUpdate,
    WorkspaceMemberResponse,
    WorkspaceStats,
    WorkspaceActivity,
    WorkspaceType,
    WorkspaceVisibility,
    MemberRole,
)

# Agent schemas
from backend.src.schemas.agent import (
    AgentBase,
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentListResponse,
    AgentVersionResponse,
    AgentExecutionCreate,
    AgentExecutionResponse,
    AgentExecutionListResponse,
    AgentPromptTemplate,
    AgentMetrics,
    AgentType,
    AgentStatus,
    ExecutionStatus,
    AgentCapability,
)

# Prompt schemas
from backend.src.schemas.prompt import (
    PromptTemplateBase,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplateListResponse,
    PromptExecutionRequest,
    PromptExecutionResponse,
    PromptTemplateVersion,
    PromptTemplateRating,
    PromptLibraryFilter,
    PromptCategory,
)

__all__ = [
    # Common
    "SortDirection",
    "TimestampMixin",
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "HealthResponse",
    # Auth
    "Token",
    "TokenPayload",
    "UserLogin",
    "UserRegister",
    "PasswordReset",
    "PasswordResetConfirm",
    "RefreshTokenRequest",
    "EmailVerification",
    "PasswordChange",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "UserProfile",
    "UserProfileUpdate",
    "UserRole",
    "UserStatus",
    # Organization
    "OrganizationBase",
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "OrganizationListResponse",
    "OrganizationStats",
    "OrganizationMember",
    "OrganizationInvite",
    "OrganizationPlan",
    "OrganizationStatus",
    # Workspace
    "WorkspaceBase",
    "WorkspaceCreate",
    "WorkspaceUpdate",
    "WorkspaceResponse",
    "WorkspaceListResponse",
    "WorkspaceMemberCreate",
    "WorkspaceMemberUpdate",
    "WorkspaceMemberResponse",
    "WorkspaceStats",
    "WorkspaceActivity",
    "WorkspaceType",
    "WorkspaceVisibility",
    "MemberRole",
    # Agent
    "AgentBase",
    "AgentCreate",
    "AgentUpdate",
    "AgentResponse",
    "AgentListResponse",
    "AgentVersionResponse",
    "AgentExecutionCreate",
    "AgentExecutionResponse",
    "AgentExecutionListResponse",
    "AgentPromptTemplate",
    "AgentMetrics",
    "AgentType",
    "AgentStatus",
    "ExecutionStatus",
    "AgentCapability",
    # Prompt
    "PromptTemplateBase",
    "PromptTemplateCreate",
    "PromptTemplateUpdate",
    "PromptTemplateResponse",
    "PromptTemplateListResponse",
    "PromptExecutionRequest",
    "PromptExecutionResponse",
    "PromptTemplateVersion",
    "PromptTemplateRating",
    "PromptLibraryFilter",
    "PromptCategory",
]