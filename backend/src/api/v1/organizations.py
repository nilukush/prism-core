"""
Organization management API endpoints.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
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
import logging

logger = logging.getLogger(__name__)
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


@router.get("/current", response_model=OrganizationResponse)
async def get_current_organization(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> OrganizationResponse:
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
    
    return OrganizationResponse.model_validate(organization)


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


@router.patch("/current", response_model=OrganizationResponse)
async def update_organization(
    organization_update: OrganizationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> OrganizationResponse:
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
    
    return OrganizationResponse.model_validate(organization)