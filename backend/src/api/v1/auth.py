"""
Authentication API endpoints.
Implements OAuth2 password flow with JWT tokens and refresh token rotation.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from backend.src.api.deps import get_db, get_current_user
from backend.src.core.config import settings
from backend.src.core.logging import get_logger
from backend.src.models.user import User, UserStatus
from backend.src.schemas.auth import (
    Token, UserRegister, UserResponse, PasswordReset,
    PasswordResetConfirm, RefreshTokenRequest, EmailVerification,
    PasswordChange
)
from backend.src.services.auth import AuthService
try:
    from backend.src.services.email_service import email_service
except ImportError:
    from backend.src.services.email_simple import email_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    
    Returns the authenticated user's profile.
    """
    return UserResponse.model_validate(current_user)


@router.get("/debug/token", include_in_schema=False)
async def debug_token(
    current_user: User = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """Debug endpoint to check token status."""
    token_info = {}
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = AuthService.decode_token(token)
            token_info = {
                "valid": True,
                "user_id": payload.sub,
                "type": payload.type,
                "expires_at": datetime.fromtimestamp(payload.exp).isoformat() if hasattr(payload, 'exp') else None,
                "issued_at": datetime.fromtimestamp(payload.iat).isoformat() if hasattr(payload, 'iat') else None,
            }
        except Exception as e:
            token_info = {
                "valid": False,
                "error": str(e)
            }
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "status": current_user.status,
            "is_active": current_user.is_active
        },
        "token": token_info,
        "server_time": datetime.now(timezone.utc).isoformat()
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Register a new user.
    
    - Creates user account with hashed password
    - Sends email verification
    - Returns user profile
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if user_data.username:
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        password_hash=AuthService.hash_password(user_data.password),
        status=UserStatus.pending
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Create verification token
    verification_token = AuthService.create_email_verification_token(
        user_id=user.id,
        email=user.email
    )
    
    # Send verification email in background
    background_tasks.add_task(
        email_service.send_verification_email,
        email=user.email,
        username=user.username or user.email,
        verification_token=verification_token
    )
    
    logger.info("user_registered", user_id=user.id, email=user.email)
    
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    OAuth2 compatible token login.
    
    - Accepts username (email or username) and password
    - Returns access and refresh tokens
    - Implements refresh token rotation
    """
    # Authenticate user
    user = await AuthService.authenticate_user(
        db=db,
        username=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Load roles
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user.id)
    )
    user = result.scalar_one()
    
    # Get user roles
    roles = [role.name for role in user.roles]
    
    # Create tokens
    access_token, access_exp = AuthService.create_access_token(
        user_id=user.id,
        email=user.email,
        roles=roles
    )
    
    refresh_token, family_id, refresh_exp = AuthService.create_refresh_token(
        user_id=user.id
    )
    
    # Calculate expiry times in seconds
    access_expires_in = int((access_exp - datetime.now(access_exp.tzinfo)).total_seconds())
    refresh_expires_in = int((refresh_exp - datetime.now(refresh_exp.tzinfo)).total_seconds())
    
    logger.info("user_login", user_id=user.id, family_id=family_id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=access_expires_in,
        refresh_expires_in=refresh_expires_in
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Refresh access token using refresh token.
    
    - Implements refresh token rotation
    - Detects token reuse and revokes token family
    - Returns new access and refresh tokens
    """
    try:
        access_token, refresh_token, access_exp, refresh_exp = await AuthService.refresh_access_token(
            db=db,
            refresh_token=refresh_request.refresh_token
        )
        
        # Calculate expiry times in seconds
        access_expires_in = int((access_exp - datetime.now(access_exp.tzinfo)).total_seconds())
        refresh_expires_in = int((refresh_exp - datetime.now(refresh_exp.tzinfo)).total_seconds())
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=access_expires_in,
            refresh_expires_in=refresh_expires_in
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("token_refresh_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    authorization: Annotated[str, Header()] = None
):
    """
    Logout current user.
    
    - Revokes current access token
    - Revokes all refresh tokens for the user
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        # Revoke token
        AuthService.revoke_token(token)
    
    # Revoke all user refresh tokens
    AuthService.revoke_all_user_tokens(current_user.id)
    
    logger.info("user_logout", user_id=current_user.id)


@router.post("/verify-email", response_model=UserResponse)
async def verify_email(
    verification: EmailVerification,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Verify email address.
    
    - Validates verification token
    - Activates user account
    - Returns updated user profile
    """
    user = await AuthService.verify_email_token(
        db=db,
        token=verification.token
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    logger.info("email_verified", user_id=user.id)
    
    return UserResponse.model_validate(user)


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
async def resend_verification(
    email: str,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Resend email verification.
    
    - Creates new verification token
    - Sends verification email
    """
    # Get user
    result = await db.execute(
        select(User).where(
            and_(
                User.email == email,
                User.email_verified == False
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists
        return
    
    # Create new verification token
    verification_token = AuthService.create_email_verification_token(
        user_id=user.id,
        email=user.email
    )
    
    # Send verification email
    background_tasks.add_task(
        email_service.send_verification_email,
        email=user.email,
        username=user.username or user.email,
        verification_token=verification_token
    )
    
    logger.info("verification_resent", user_id=user.id)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    password_reset: PasswordReset,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Request password reset.
    
    - Creates password reset token
    - Sends reset email
    """
    # Get user
    result = await db.execute(
        select(User).where(User.email == password_reset.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists
        return
    
    # Create reset token
    reset_token = AuthService.create_password_reset_token(
        user_id=user.id,
        email=user.email
    )
    
    # Send reset email
    background_tasks.add_task(
        email_service.send_password_reset_email,
        email=user.email,
        username=user.username or user.email,
        reset_token=reset_token
    )
    
    logger.info("password_reset_requested", user_id=user.id)


@router.post("/reset-password", response_model=UserResponse)
async def reset_password(
    reset_confirm: PasswordResetConfirm,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Reset password with token.
    
    - Validates reset token
    - Updates password
    - Revokes all user tokens
    """
    user = await AuthService.reset_password(
        db=db,
        token=reset_confirm.token,
        new_password=reset_confirm.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    logger.info("password_reset", user_id=user.id)
    
    return UserResponse.model_validate(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_change: PasswordChange,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Change password for authenticated user.
    
    - Validates current password
    - Updates to new password
    - Revokes all tokens
    """
    # Verify current password
    if not AuthService.verify_password(password_change.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.password_hash = AuthService.hash_password(password_change.new_password)
    
    # Revoke all tokens
    AuthService.revoke_all_user_tokens(current_user.id)
    
    await db.commit()
    
    logger.info("password_changed", user_id=current_user.id)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get current user information.
    
    - Returns authenticated user profile
    - Includes roles and permissions
    """
    return UserResponse.model_validate(current_user)