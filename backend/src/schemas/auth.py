"""
Authentication schemas.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class Token(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class TokenPayload(BaseModel):
    """Token payload."""
    sub: str
    exp: int
    iat: int
    type: str
    jti: Optional[str] = None
    email: Optional[str] = None
    roles: Optional[List[str]] = None
    family: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    username: str = Field(..., description="Email or username")
    password: str = Field(..., min_length=6)


class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserResponse(BaseModel):
    """User response."""
    id: int
    email: str
    username: Optional[str]
    full_name: Optional[str]
    is_active: bool
    email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    token: str
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class PasswordChange(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class EmailVerification(BaseModel):
    """Email verification request."""
    token: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str