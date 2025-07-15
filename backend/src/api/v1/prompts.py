"""
Prompt template management API endpoints.
"""

from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.src.core.database import get_db
from backend.src.api.deps import get_current_user, PermissionChecker
from backend.src.api.deps import require_permissions
from backend.src.models.user import User
from backend.src.models.prompt import PromptTemplate
from backend.src.schemas.prompt import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplateListResponse
)
from backend.src.schemas.common import SortDirection
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prompts")


@router.get("", response_model=PromptTemplateListResponse)
async def list_prompt_templates(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: Annotated[Optional[str], Query()] = None,
    # Filtering
    category: Annotated[Optional[str], Query()] = None,
    is_public: Annotated[Optional[bool], Query()] = None,
    search: Annotated[Optional[str], Query(max_length=100)] = None,
    # Sorting
    sort_by: str = "created_at",
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.DESC,
) -> PromptTemplateListResponse:
    """
    List prompt templates accessible to the current user.
    """
    # Base query - user can see public templates and their own/org templates
    query = select(PromptTemplate).options(
        selectinload(PromptTemplate.created_by)
    )
    
    # Filter by visibility
    if is_public is not None:
        query = query.where(PromptTemplate.is_public == is_public)
    else:
        # Show public templates and user's organization templates
        query = query.where(
            (PromptTemplate.is_public == True) |
            (PromptTemplate.organization_id == current_user.organization_id)
        )
    
    # Apply filters
    if category:
        query = query.where(PromptTemplate.category == category)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (PromptTemplate.name.ilike(search_pattern)) |
            (PromptTemplate.description.ilike(search_pattern))
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query)
    
    # Apply cursor pagination
    if cursor:
        cursor_id = cursor
        if sort_direction == SortDirection.DESC:
            query = query.where(PromptTemplate.id < cursor_id)
        else:
            query = query.where(PromptTemplate.id > cursor_id)
    
    # Apply sorting
    order_field = getattr(PromptTemplate, sort_by)
    if sort_direction == SortDirection.DESC:
        query = query.order_by(order_field.desc())
    else:
        query = query.order_by(order_field.asc())
    
    # Apply limit
    query = query.limit(limit + 1)
    
    # Execute query
    result = await db.execute(query)
    templates = result.scalars().all()
    
    # Determine pagination info
    has_next = len(templates) > limit
    if has_next:
        templates = templates[:-1]
    
    return PromptTemplateListResponse(
        data=[PromptTemplateResponse.model_validate(t) for t in templates],
        pagination={
            "has_next": has_next,
            "has_previous": cursor is not None,
            "next_cursor": str(templates[-1].id) if has_next and templates else None,
            "total_count": total_count
        }
    )


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> PromptTemplateResponse:
    """Get a specific prompt template."""
    result = await db.execute(
        select(PromptTemplate).options(
            selectinload(PromptTemplate.created_by)
        ).where(PromptTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    # Check access - public or same organization
    if not template.is_public and template.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return PromptTemplateResponse.model_validate(template)


@router.post("", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt_template(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    template_data: PromptTemplateCreate
) -> PromptTemplateResponse:
    """
    Create a new prompt template.
    
    Requires: agents:write permission for public templates
    """
    # Only users with agents:write can create public templates
    if template_data.is_public:
        require_permissions(current_user, ["agents:write"])
    
    template = PromptTemplate(
        name=template_data.name,
        description=template_data.description,
        content=template_data.content,
        variables=template_data.variables,
        category=template_data.category,
        is_public=template_data.is_public,
        created_by_id=current_user.id,
        organization_id=current_user.organization_id
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template, ["created_by"])
    
    logger.info(
        "prompt_template_created",
        template_id=str(template.id),
        created_by=str(current_user.id),
        is_public=template.is_public
    )
    
    return PromptTemplateResponse.model_validate(template)


@router.patch("/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: str,
    template_update: PromptTemplateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> PromptTemplateResponse:
    """Update a prompt template."""
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    # Check ownership
    if template.created_by_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own templates"
        )
    
    # Apply updates
    update_data = template_update.model_dump(exclude_unset=True)
    
    # Only superusers can change public status
    if "is_public" in update_data and not current_user.is_superuser:
        update_data.pop("is_public")
    
    for field, value in update_data.items():
        setattr(template, field, value)
    
    await db.commit()
    await db.refresh(template, ["created_by"])
    
    logger.info(
        "prompt_template_updated",
        template_id=template_id,
        updated_by=str(current_user.id),
        fields=list(update_data.keys())
    )
    
    return PromptTemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt_template(
    template_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Delete a prompt template."""
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    # Check ownership
    if template.created_by_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own templates"
        )
    
    await db.delete(template)
    await db.commit()
    
    logger.info(
        "prompt_template_deleted",
        template_id=template_id,
        deleted_by=str(current_user.id)
    )