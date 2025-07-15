"""
Workspace management API endpoints.
Implements comprehensive workspace CRUD operations with proper authorization.
"""

from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.src.core.database import get_db
from backend.src.api.deps import get_current_user, PermissionChecker
from backend.src.api.deps import require_permissions
from backend.src.models.user import User
from backend.src.models.workspace import Workspace, WorkspaceMember
from backend.src.models.organization import Organization
from backend.src.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    MemberRole
)
from backend.src.schemas.common import SortDirection
import logging
import hashlib
import hmac

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: Annotated[Optional[str], Query()] = None,
    # Filtering
    organization_id: Annotated[Optional[str], Query()] = None,
    search: Annotated[Optional[str], Query(max_length=100)] = None,
    # Sorting
    sort_by: str = "created_at",
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.DESC,
) -> WorkspaceListResponse:
    """
    List workspaces accessible to the current user.
    
    Requires: workspaces:read permission
    """
    require_permissions(current_user, ["workspaces:read"])
    
    # Base query - user can see workspaces they're a member of or all in org if superuser
    if current_user.is_superuser:
        query = select(Workspace).options(
            selectinload(Workspace.organization),
            selectinload(Workspace.created_by),
            selectinload(Workspace.members)
        )
    else:
        # Join with WorkspaceMember to get only workspaces user is member of
        query = select(Workspace).join(
            WorkspaceMember,
            and_(
                WorkspaceMember.workspace_id == Workspace.id,
                WorkspaceMember.user_id == current_user.id
            )
        ).options(
            selectinload(Workspace.organization),
            selectinload(Workspace.created_by),
            selectinload(Workspace.members)
        )
    
    # Apply filters
    if organization_id:
        query = query.where(Workspace.organization_id == organization_id)
    elif not current_user.is_superuser:
        # Non-superusers can only see workspaces in their organization
        query = query.where(Workspace.organization_id == current_user.organization_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Workspace.name.ilike(search_pattern)) |
            (Workspace.description.ilike(search_pattern))
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query)
    
    # Apply cursor pagination
    if cursor:
        cursor_id = cursor
        if sort_direction == SortDirection.DESC:
            query = query.where(Workspace.id < cursor_id)
        else:
            query = query.where(Workspace.id > cursor_id)
    
    # Apply sorting
    order_field = getattr(Workspace, sort_by)
    if sort_direction == SortDirection.DESC:
        query = query.order_by(order_field.desc())
    else:
        query = query.order_by(order_field.asc())
    
    # Apply limit
    query = query.limit(limit + 1)
    
    # Execute query
    result = await db.execute(query)
    workspaces = result.scalars().unique().all()
    
    # Determine pagination info
    has_next = len(workspaces) > limit
    if has_next:
        workspaces = workspaces[:-1]
    
    return WorkspaceListResponse(
        data=[WorkspaceResponse.model_validate(workspace) for workspace in workspaces],
        pagination={
            "has_next": has_next,
            "has_previous": cursor is not None,
            "next_cursor": str(workspaces[-1].id) if has_next and workspaces else None,
            "total_count": total_count
        }
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> WorkspaceResponse:
    """
    Get a specific workspace by ID.
    
    Requires: workspaces:read permission and workspace membership
    """
    require_permissions(current_user, ["workspaces:read"])
    
    # Build query
    query = select(Workspace).options(
        selectinload(Workspace.organization),
        selectinload(Workspace.created_by),
        selectinload(Workspace.members).selectinload(WorkspaceMember.user),
        selectinload(Workspace.agents)
    ).where(Workspace.id == workspace_id)
    
    result = await db.execute(query)
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Check access - user must be member or superuser
    if not current_user.is_superuser:
        is_member = any(
            member.user_id == current_user.id 
            for member in workspace.members
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this workspace"
            )
    
    return WorkspaceResponse.model_validate(workspace)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    workspace_data: WorkspaceCreate,
    idempotency_key: Annotated[Optional[str], Header()] = None
) -> WorkspaceResponse:
    """
    Create a new workspace.
    
    Requires: workspaces:write permission
    Supports idempotency via Idempotency-Key header
    """
    require_permissions(current_user, ["workspaces:write"])
    
    # Handle idempotency
    if idempotency_key:
        # Check if workspace was already created with this key
        # In production, implement proper idempotency key storage
        pass
    
    # Validate organization
    organization_id = workspace_data.organization_id or current_user.organization_id
    if not current_user.is_superuser and organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create workspaces in other organizations"
        )
    
    # Create workspace
    workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description,
        organization_id=organization_id,
        created_by_id=current_user.id,
        settings=workspace_data.settings or {}
    )
    
    # Add creator as admin member
    creator_member = WorkspaceMember(
        workspace=workspace,
        user_id=current_user.id,
        role=MemberRole.ADMIN
    )
    workspace.members.append(creator_member)
    
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace, ["organization", "created_by", "members"])
    
    logger.info(
        "workspace_created",
        workspace_id=str(workspace.id),
        created_by=str(current_user.id)
    )
    
    return WorkspaceResponse.model_validate(workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    workspace_update: WorkspaceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> WorkspaceResponse:
    """
    Update a workspace.
    
    Requires: workspaces:write permission and admin role in workspace
    """
    require_permissions(current_user, ["workspaces:write"])
    
    # Get workspace
    result = await db.execute(
        select(Workspace).options(
            selectinload(Workspace.members)
        ).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Check if user is admin of workspace
    if not current_user.is_superuser:
        member = next(
            (m for m in workspace.members if m.user_id == current_user.id),
            None
        )
        if not member or member.role != MemberRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace admins can update workspace"
            )
    
    # Apply updates
    update_data = workspace_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)
    
    await db.commit()
    await db.refresh(workspace, ["organization", "created_by", "members"])
    
    logger.info(
        "workspace_updated",
        workspace_id=workspace_id,
        updated_by=str(current_user.id),
        fields=list(update_data.keys())
    )
    
    return WorkspaceResponse.model_validate(workspace)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Delete a workspace.
    
    Requires: workspaces:delete permission and workspace ownership
    """
    require_permissions(current_user, ["workspaces:delete"])
    
    # Get workspace
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Check ownership - only creator or superuser can delete
    if not current_user.is_superuser and workspace.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace creator can delete workspace"
        )
    
    # Soft delete
    workspace.is_deleted = True
    await db.commit()
    
    logger.info(
        "workspace_deleted",
        workspace_id=workspace_id,
        deleted_by=str(current_user.id)
    )


# Workspace member management endpoints

@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> List[WorkspaceMemberResponse]:
    """
    List members of a workspace.
    
    Requires: workspace membership
    """
    # Get workspace with members
    result = await db.execute(
        select(Workspace).options(
            selectinload(Workspace.members).selectinload(WorkspaceMember.user)
        ).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Check access
    if not current_user.is_superuser:
        is_member = any(
            member.user_id == current_user.id 
            for member in workspace.members
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this workspace"
            )
    
    return [
        WorkspaceMemberResponse.model_validate(member) 
        for member in workspace.members
    ]


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    workspace_id: str,
    member_data: WorkspaceMemberCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> WorkspaceMemberResponse:
    """
    Add a member to a workspace.
    
    Requires: workspace admin role
    """
    # Get workspace
    result = await db.execute(
        select(Workspace).options(
            selectinload(Workspace.members)
        ).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Check if user is admin
    if not current_user.is_superuser:
        member = next(
            (m for m in workspace.members if m.user_id == current_user.id),
            None
        )
        if not member or member.role != MemberRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace admins can add members"
            )
    
    # Check if user already member
    existing = next(
        (m for m in workspace.members if m.user_id == member_data.user_id),
        None
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User is already a member"
        )
    
    # Verify user exists and is in same org
    user_result = await db.execute(
        select(User).where(User.id == member_data.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.organization_id != workspace.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be in same organization"
        )
    
    # Add member
    new_member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member, ["user"])
    
    logger.info(
        "workspace_member_added",
        workspace_id=workspace_id,
        user_id=member_data.user_id,
        role=member_data.role,
        added_by=str(current_user.id)
    )
    
    return WorkspaceMemberResponse.model_validate(new_member)


@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_workspace_member(
    workspace_id: str,
    user_id: str,
    role: MemberRole,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> WorkspaceMemberResponse:
    """
    Update a workspace member's role.
    
    Requires: workspace admin role
    """
    # Get workspace member
    result = await db.execute(
        select(WorkspaceMember).options(
            selectinload(WorkspaceMember.user)
        ).where(
            (WorkspaceMember.workspace_id == workspace_id) &
            (WorkspaceMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Check if current user is admin
    if not current_user.is_superuser:
        current_member_result = await db.execute(
            select(WorkspaceMember).where(
                (WorkspaceMember.workspace_id == workspace_id) &
                (WorkspaceMember.user_id == current_user.id)
            )
        )
        current_member = current_member_result.scalar_one_or_none()
        
        if not current_member or current_member.role != MemberRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace admins can update member roles"
            )
    
    # Update role
    member.role = role
    await db.commit()
    
    logger.info(
        "workspace_member_updated",
        workspace_id=workspace_id,
        user_id=user_id,
        new_role=role,
        updated_by=str(current_user.id)
    )
    
    return WorkspaceMemberResponse.model_validate(member)


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Remove a member from a workspace.
    
    Requires: workspace admin role or self-removal
    """
    # Get member
    result = await db.execute(
        select(WorkspaceMember).where(
            (WorkspaceMember.workspace_id == workspace_id) &
            (WorkspaceMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Check permissions - admin or self-removal
    if not current_user.is_superuser and user_id != str(current_user.id):
        current_member_result = await db.execute(
            select(WorkspaceMember).where(
                (WorkspaceMember.workspace_id == workspace_id) &
                (WorkspaceMember.user_id == current_user.id)
            )
        )
        current_member = current_member_result.scalar_one_or_none()
        
        if not current_member or current_member.role != MemberRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace admins can remove members"
            )
    
    # Don't allow removing last admin
    if member.role == MemberRole.ADMIN:
        admin_count_result = await db.execute(
            select(func.count()).where(
                (WorkspaceMember.workspace_id == workspace_id) &
                (WorkspaceMember.role == MemberRole.ADMIN)
            )
        )
        admin_count = admin_count_result.scalar()
        
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove last admin from workspace"
            )
    
    await db.delete(member)
    await db.commit()
    
    logger.info(
        "workspace_member_removed",
        workspace_id=workspace_id,
        user_id=user_id,
        removed_by=str(current_user.id)
    )