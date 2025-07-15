"""
User-related Pydantic schemas.
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from pydantic.functional_validators import field_validator

from backend.src.schemas.common import TimestampMixin, PaginatedResponse, SortDirection


class UserRole(str, Enum):
    """User role enum."""
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr = Field(description="User email address")
    full_name: str = Field(min_length=1, max_length=255, description="User full name")
    is_active: bool = Field(default=True, description="Whether user is active")
    
    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(min_length=8, max_length=100, description="User password")
    role: Optional[UserRole] = Field(default=UserRole.MEMBER, description="User role")
    organization_id: Optional[UUID] = Field(default=None, description="Organization ID")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = Field(default=None, description="User email address")
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = Field(default=None)
    role: Optional[UserRole] = Field(default=None)
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserBase):
    """User schema for database representation."""
    id: UUID
    hashed_password: str
    organization_id: Optional[UUID] = None
    email_verified: bool = False
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase, TimestampMixin):
    """User response schema."""
    id: UUID
    organization_id: Optional[UUID] = None
    organization_name: Optional[str] = None
    email_verified: bool = False
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    roles: List[str] = Field(default_factory=list, description="User roles")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    avatar_url: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(PaginatedResponse[UserResponse]):
    """Paginated user list response."""
    pass


class UserProfile(BaseModel):
    """User profile information."""
    id: UUID
    email: EmailStr
    full_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=500)
    location: Optional[str] = Field(default=None, max_length=100)
    timezone: Optional[str] = Field(default="UTC")
    language: Optional[str] = Field(default="en")
    preferences: Optional[dict] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=500)
    location: Optional[str] = Field(default=None, max_length=100)
    timezone: Optional[str] = None
    language: Optional[str] = None
    preferences: Optional[dict] = None