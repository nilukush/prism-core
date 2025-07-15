"""
Projects API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from backend.src.core.database import get_db
from backend.src.models.user import User
from backend.src.models.project import Project, ProjectStatus
from backend.src.models.organization import Organization, OrganizationMember
from backend.src.api.deps import get_current_user
from backend.src.core.logging import get_logger
from backend.src.schemas.project_simple import ProjectCreateSimple, ProjectUpdateSimple

logger = get_logger(__name__)

router = APIRouter()


@router.get("/")
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    project_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all projects the current user has access to.
    
    This includes:
    - Projects where the user is the owner
    - Projects in organizations where the user is a member
    - Projects in workspaces the user has access to
    """
    try:
        # Build query to get projects user has access to
        # For now, we'll get projects where:
        # 1. User is the owner
        # 2. User is a member of the project's organization
        
        # Get user's organizations
        org_query = select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == current_user.id
        )
        org_result = await db.execute(org_query)
        user_org_ids = [row[0] for row in org_result.fetchall()]
        
        # Build project query
        query = select(Project).where(
            and_(
                Project.is_deleted == False,
                or_(
                    Project.owner_id == current_user.id,
                    Project.organization_id.in_(user_org_ids) if user_org_ids else False
                )
            )
        )
        
        # Apply status filter if provided
        if project_status:
            try:
                status_enum = ProjectStatus(project_status)
                query = query.where(Project.status == status_enum)
            except ValueError:
                logger.warning(f"Invalid project status filter: {project_status}")
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query with eager loading of relationships
        query = query.options(
            selectinload(Project.owner),
            selectinload(Project.organization)
        )
        result = await db.execute(query)
        projects = result.scalars().all()
        
        # Count total
        count_query = select(Project).where(
            and_(
                Project.is_deleted == False,
                or_(
                    Project.owner_id == current_user.id,
                    Project.organization_id.in_(user_org_ids) if user_org_ids else False
                )
            )
        )
        if project_status:
            try:
                status_enum = ProjectStatus(project_status)
                count_query = count_query.where(Project.status == status_enum)
            except ValueError:
                pass
                
        count_result = await db.execute(count_query)
        total = len(count_result.all())
        
        # Format response
        project_list = [
            {
                "id": project.id,
                "name": project.name,
                "key": project.key,
                "description": project.description,
                "status": project.status.value,
                "organization_id": project.organization_id,
                "organization": {
                    "id": project.organization.id,
                    "name": project.organization.name
                } if project.organization else None,
                "workspace_id": project.workspace_id,
                "owner_id": project.owner_id,
                "owner": {
                    "id": project.owner.id,
                    "full_name": project.owner.full_name,
                    "email": project.owner.email
                } if project.owner else None,
                "start_date": project.start_date.isoformat() if project.start_date else None,
                "target_end_date": project.target_end_date.isoformat() if project.target_end_date else None,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            }
            for project in projects
        ]
        
        logger.info(
            "projects_listed",
            user_id=current_user.id,
            count=len(project_list),
            total=total
        )
        
        return JSONResponse(
            content={
                "projects": project_list,
                "total": total,
                "skip": skip,
                "limit": limit,
                "status": project_status
            }
        )
        
    except Exception as e:
        logger.error("projects_list_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}"
        )


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get a specific project by ID.
    """
    # TODO: Implement project retrieval logic
    return {
        "id": project_id,
        "name": "Sample Project",
        "description": "This is a placeholder project.",
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@router.post("/")
async def create_project(
    project_data: ProjectCreateSimple,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create a new project.
    """
    try:
        # Check if user has access to the organization
        org_member_query = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == project_data.organization_id,
                OrganizationMember.user_id == current_user.id
            )
        )
        org_member_result = await db.execute(org_member_query)
        org_member = org_member_result.scalar_one_or_none()
        
        # If not a member, check if they own the organization
        if not org_member:
            org_query = select(Organization).where(
                and_(
                    Organization.id == project_data.organization_id,
                    Organization.owner_id == current_user.id
                )
            )
            org_result = await db.execute(org_query)
            organization = org_result.scalar_one_or_none()
            
            if not organization:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to create projects in this organization"
                )
        
        # Check if project key already exists in organization
        existing_query = select(Project).where(
            and_(
                Project.organization_id == project_data.organization_id,
                Project.key == project_data.key,
                Project.is_deleted == False
            )
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project with key '{project_data.key}' already exists in this organization"
            )
        
        # Create the project
        new_project = Project(
            name=project_data.name,
            key=project_data.key,
            description=project_data.description,
            status=ProjectStatus(project_data.status),
            organization_id=project_data.organization_id,
            owner_id=current_user.id,
            start_date=project_data.start_date,
            target_end_date=project_data.target_end_date
        )
        
        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)
        
        logger.info(
            "project_created",
            project_id=new_project.id,
            project_key=new_project.key,
            user_id=current_user.id
        )
        
        return {
            "id": new_project.id,
            "name": new_project.name,
            "key": new_project.key,
            "description": new_project.description,
            "status": new_project.status.value,
            "organization_id": new_project.organization_id,
            "owner_id": new_project.owner_id,
            "start_date": new_project.start_date.isoformat() if new_project.start_date else None,
            "target_end_date": new_project.target_end_date.isoformat() if new_project.target_end_date else None,
            "created_at": new_project.created_at.isoformat(),
            "message": "Project created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("project_creation_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.put("/{project_id}")
async def update_project(
    project_id: int,
    project_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Update a project.
    """
    # TODO: Implement project update logic
    return {
        "id": project_id,
        "name": project_data.get("name", "Updated Project"),
        "description": project_data.get("description", ""),
        "status": project_data.get("status", "active"),
        "message": "Project updated successfully",
    }


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Delete a project.
    """
    # TODO: Implement project deletion logic
    return {
        "message": f"Project {project_id} deleted successfully",
    }