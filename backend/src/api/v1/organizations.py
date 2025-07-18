"""
Organization management API endpoints.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.src.core.database import get_db
from backend.src.api.deps import get_current_user, PermissionChecker
from backend.src.api.deps import require_permissions
from backend.src.models.user import User
from backend.src.models.organization import Organization, OrganizationMember
from backend.src.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationStats
)
from backend.src.schemas.common import SortDirection
from backend.src.models.organization import OrganizationPlan
from backend.src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_organizations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """List all organizations the current user belongs to."""
    try:
        # Get organizations where user is owner
        owner_query = select(Organization).where(Organization.owner_id == current_user.id)
        
        # Get organizations where user is member
        member_query = select(Organization).join(
            OrganizationMember, 
            Organization.id == OrganizationMember.organization_id
        ).where(OrganizationMember.user_id == current_user.id)
        
        # Execute both queries
        owner_result = await db.execute(owner_query)
        member_result = await db.execute(member_query)
        
        # Combine results and remove duplicates
        organizations = []
        org_ids = set()
        
        for org in owner_result.scalars().all():
            if org.id not in org_ids:
                organizations.append(org)
                org_ids.add(org.id)
                
        for org in member_result.scalars().all():
            if org.id not in org_ids:
                organizations.append(org)
                org_ids.add(org.id)
        
        # Format response
        return {
            "organizations": [
                {
                    "id": org.id,
                    "name": org.name,
                    "slug": org.slug,
                    "plan": org.plan.value,
                    "max_projects": org.max_projects,
                    "is_owner": org.owner_id == current_user.id
                }
                for org in organizations
            ],
            "total": len(organizations)
        }
    except Exception as e:
        logger.error("list_organizations_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list organizations: {str(e)}"
        )


@router.post("/")
async def create_organization(
    organization_data: OrganizationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Create a new organization.
    
    The current user will be set as the owner and added as an admin member.
    """
    try:
        # Check if slug already exists
        existing = await db.execute(
            select(Organization).where(Organization.slug == organization_data.slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization with slug '{organization_data.slug}' already exists"
            )
        
        # Create organization
        new_org = Organization(
            name=organization_data.name,
            slug=organization_data.slug,
            description=organization_data.description,
            email=current_user.email,  # Use owner's email as org email
            plan=organization_data.plan if hasattr(organization_data, 'plan') else OrganizationPlan.FREE,
            owner_id=current_user.id,
            max_users=10,  # Default for free plan
            max_projects=5,  # Default for free plan
            max_storage_gb=10  # Default for free plan
        )
        
        db.add(new_org)
        await db.flush()  # Get the ID without committing
        
        # Add the owner as an admin member
        org_member = OrganizationMember(
            organization_id=new_org.id,
            user_id=current_user.id,
            role="admin"
        )
        db.add(org_member)
        
        await db.commit()
        await db.refresh(new_org)
        
        logger.info(
            "organization_created",
            organization_id=new_org.id,
            slug=new_org.slug,
            owner_id=current_user.id
        )
        
        # Return simple dict to avoid UUID/int mismatch
        return {
            "id": new_org.id,
            "name": new_org.name,
            "slug": new_org.slug,
            "description": new_org.description,
            "plan": new_org.plan.value,
            "owner_id": new_org.owner_id,
            "max_users": new_org.max_users,
            "max_projects": new_org.max_projects,
            "created_at": new_org.created_at.isoformat() if new_org.created_at else None,
            "updated_at": new_org.updated_at.isoformat() if new_org.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_organization_failed", error=str(e), user_id=current_user.id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}"
        )


@router.get("/current")
async def get_current_organization(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current user's organization."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no organization"
        )
    
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "plan": organization.plan.value
    }


@router.get("/current/stats", response_model=OrganizationStats)
async def get_organization_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> OrganizationStats:
    """Get organization statistics."""
    require_permissions(current_user, ["analytics:read"])
    
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no organization"
        )
    
    # Get counts
    user_count = await db.scalar(
        select(func.count()).select_from(User).where(
            User.organization_id == current_user.organization_id
        )
    )
    
    # Would include other stats like workspace_count, agent_count, etc.
    
    return OrganizationStats(
        user_count=user_count,
        workspace_count=0,  # Placeholder
        agent_count=0,      # Placeholder
        active_users_30d=0, # Placeholder
        storage_used_mb=0   # Placeholder
    )


@router.patch("/current")
async def update_organization(
    organization_update: OrganizationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Update organization settings.
    
    Requires: org:manage permission
    """
    require_permissions(current_user, ["org:manage"])
    
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no organization"
        )
    
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Apply updates
    update_data = organization_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    await db.commit()
    await db.refresh(organization)
    
    logger.info(
        "organization_updated",
        organization_id=str(organization.id),
        updated_by=str(current_user.id),
        fields=list(update_data.keys())
    )
    
    return {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "plan": organization.plan.value,
        "updated_at": organization.updated_at.isoformat() if organization.updated_at else None
    }


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Delete an organization.
    
    Only the organization owner can delete it.
    This will cascade delete all related data (projects, members, etc.)
    """
    # Check if organization exists and user is owner
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        # Return 204 for idempotent delete (organization already deleted)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    # Check if user is the owner
    if organization.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the organization owner can delete it"
        )
    
    # Log the deletion
    logger.warning(
        "organization_deletion",
        organization_id=organization_id,
        organization_slug=organization.slug,
        deleted_by=current_user.id
    )
    
    # Delete the organization (cascade will handle related data)
    await db.delete(organization)
    await db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)