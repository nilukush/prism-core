"""
User management API endpoints.
Implements RESTful patterns with comprehensive user CRUD operations.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.src.core.database import get_db
from backend.src.api.deps import get_current_user, PermissionChecker
from backend.src.api.deps import require_permissions
from backend.src.models.user import User, Role
from backend.src.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    SortDirection
)
from backend.src.services.auth import AuthService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=UserListResponse)
async def list_users(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: Annotated[Optional[str], Query()] = None,
    # Filtering
    organization_id: Annotated[Optional[str], Query()] = None,
    is_active: Annotated[Optional[bool], Query()] = None,
    is_verified: Annotated[Optional[bool], Query()] = None,
    search: Annotated[Optional[str], Query(max_length=100)] = None,
    # Sorting
    sort_by: str = "created_at",
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.DESC,
) -> UserListResponse:
    """
    List users with pagination, filtering, and sorting.
    
    Requires: users:read permission
    """
    # Check permissions
    require_permissions(current_user, ["users:read"])
    
    # Build base query
    query = select(User).options(
        selectinload(User.organization),
        selectinload(User.roles)
    )
    
    # Apply filters
    if organization_id:
        query = query.where(User.organization_id == organization_id)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if is_verified is not None:
        query = query.where(User.is_verified == is_verified)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_pattern)) |
            (User.username.ilike(search_pattern)) |
            (User.full_name.ilike(search_pattern))
        )
    
    # Non-superusers can only see users in their organization
    if not current_user.is_superuser:
        query = query.where(User.organization_id == current_user.organization_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query)
    
    # Apply cursor pagination
    if cursor:
        # Decode cursor (simplified - in production use proper cursor encoding)
        cursor_id = cursor
        if sort_direction == SortDirection.DESC:
            query = query.where(User.id < cursor_id)
        else:
            query = query.where(User.id > cursor_id)
    
    # Apply sorting
    order_field = getattr(User, sort_by)
    if sort_direction == SortDirection.DESC:
        query = query.order_by(order_field.desc())
    else:
        query = query.order_by(order_field.asc())
    
    # Apply limit
    query = query.limit(limit + 1)  # Fetch one extra to detect hasNext
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Determine pagination info
    has_next = len(users) > limit
    if has_next:
        users = users[:-1]  # Remove the extra item
    
    # Create response
    return UserListResponse(
        data=[UserResponse.model_validate(user) for user in users],
        pagination={
            "has_next": has_next,
            "has_previous": cursor is not None,
            "next_cursor": str(users[-1].id) if has_next and users else None,
            "total_count": total_count
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    """Get current user's profile."""
    # Load relationships
    await db.refresh(current_user, ["organization", "roles"])
    return UserResponse.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> UserResponse:
    """
    Get a specific user by ID.
    
    Requires: users:read permission
    """
    require_permissions(current_user, ["users:read"])
    
    # Build query with relationships
    query = select(User).options(
        selectinload(User.organization),
        selectinload(User.roles)
    ).where(User.id == user_id)
    
    # Non-superusers can only see users in their organization
    if not current_user.is_superuser:
        query = query.where(User.organization_id == current_user.organization_id)
    
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    user_data: UserCreate
) -> UserResponse:
    """
    Create a new user.
    
    Requires: users:write permission
    """
    require_permissions(current_user, ["users:write"])
    
    # Check if email already exists
    existing = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if user_data.username:
        existing = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Username already taken"
            )
    
    # Non-superusers can only create users in their organization
    if not current_user.is_superuser and user_data.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create users in other organizations"
        )
    
    # Create user
    auth_service = AuthService()
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        organization_id=user_data.organization_id or current_user.organization_id,
        is_active=user_data.is_active,
        preferences=user_data.preferences or {}
    )
    user.hashed_password = auth_service.hash_password(user_data.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user, ["organization", "roles"])
    
    logger.info(
        "user_created",
        user_id=str(user.id),
        created_by=str(current_user.id)
    )
    
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> UserResponse:
    """
    Update a user.
    
    Requires: users:write permission or self-update
    """
    # Users can update their own profile or need users:write permission
    if user_id != str(current_user.id):
        require_permissions(current_user, ["users:write"])
    
    # Get user
    query = select(User).where(User.id == user_id)
    
    # Non-superusers can only update users in their organization
    if not current_user.is_superuser and user_id != str(current_user.id):
        query = query.where(User.organization_id == current_user.organization_id)
    
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Apply updates
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle password update
    if "password" in update_data:
        auth_service = AuthService()
        user.hashed_password = auth_service.hash_password(update_data.pop("password"))
    
    # Handle email uniqueness
    if "email" in update_data and update_data["email"] != user.email:
        existing = await db.execute(
            select(User).where(
                (User.email == update_data["email"]) & 
                (User.id != user_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Email already in use"
            )
    
    # Handle username uniqueness
    if "username" in update_data and update_data["username"] != user.username:
        existing = await db.execute(
            select(User).where(
                (User.username == update_data["username"]) & 
                (User.id != user_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Username already taken"
            )
    
    # Restrict certain fields for non-superusers
    if not current_user.is_superuser and user_id != str(current_user.id):
        restricted_fields = ["is_superuser", "is_verified", "organization_id"]
        for field in restricted_fields:
            update_data.pop(field, None)
    
    # Apply updates
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user, ["organization", "roles"])
    
    logger.info(
        "user_updated",
        user_id=user_id,
        updated_by=str(current_user.id),
        fields=list(update_data.keys())
    )
    
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Delete a user.
    
    Requires: users:delete permission
    """
    require_permissions(current_user, ["users:delete"])
    
    # Prevent self-deletion
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Get user
    query = select(User).where(User.id == user_id)
    
    # Non-superusers can only delete users in their organization
    if not current_user.is_superuser:
        query = query.where(User.organization_id == current_user.organization_id)
    
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Soft delete by deactivating
    user.is_active = False
    await db.commit()
    
    logger.info(
        "user_deleted",
        user_id=user_id,
        deleted_by=str(current_user.id)
    )


@router.post("/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def assign_role(
    user_id: str,
    role_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Assign a role to a user.
    
    Requires: admin:all permission
    """
    require_permissions(current_user, ["admin:all"])
    
    # Get user and role
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role_result = await db.execute(
        select(Role).where(Role.id == role_id)
    )
    role = role_result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Add role if not already assigned
    if role not in user.roles:
        user.roles.append(role)
        await db.commit()
    
    logger.info(
        "role_assigned",
        user_id=user_id,
        role_id=role_id,
        assigned_by=str(current_user.id)
    )


@router.delete("/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role(
    user_id: str,
    role_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Remove a role from a user.
    
    Requires: admin:all permission
    """
    require_permissions(current_user, ["admin:all"])
    
    # Get user
    user_result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Remove role if assigned
    user.roles = [r for r in user.roles if str(r.id) != role_id]
    await db.commit()
    
    logger.info(
        "role_removed",
        user_id=user_id,
        role_id=role_id,
        removed_by=str(current_user.id)
    )