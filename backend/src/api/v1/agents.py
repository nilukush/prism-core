"""
AI Agent management API endpoints.
Implements comprehensive agent CRUD operations with versioning and execution.
"""

from typing import Annotated, Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.src.core.database import get_db
from backend.src.api.deps import get_current_user, PermissionChecker
from backend.src.api.deps import require_permissions
from backend.src.models.user import User
from backend.src.models.agent import Agent, AgentVersion, AgentExecution
from backend.src.models.workspace import Workspace, WorkspaceMember
from backend.src.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentListResponse,
    AgentVersionResponse,
    AgentExecutionCreate,
    AgentExecutionResponse,
    AgentType,
    ExecutionStatus
)
from backend.src.schemas.common import SortDirection
from backend.src.services.agent_executor import AgentExecutorService
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


async def verify_workspace_access(
    workspace_id: str,
    user: User,
    db: AsyncSession,
    required_role: Optional[str] = None
) -> Workspace:
    """Verify user has access to workspace."""
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
    
    if not user.is_superuser:
        member = next(
            (m for m in workspace.members if m.user_id == user.id),
            None
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this workspace"
            )
        
        if required_role == "admin" and member.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
    
    return workspace


@router.get("", response_model=AgentListResponse)
async def list_agents(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: Annotated[Optional[str], Query()] = None,
    # Filtering
    workspace_id: Annotated[Optional[str], Query()] = None,
    type: Annotated[Optional[AgentType], Query()] = None,
    search: Annotated[Optional[str], Query(max_length=100)] = None,
    tags: Annotated[Optional[List[str]], Query()] = None,
    # Sorting
    sort_by: str = "created_at",
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.DESC,
) -> AgentListResponse:
    """
    List agents accessible to the current user.
    
    Requires: agents:read permission
    """
    require_permissions(current_user, ["agents:read"])
    
    # Base query
    query = select(Agent).options(
        selectinload(Agent.workspace).selectinload(Workspace.organization),
        selectinload(Agent.created_by),
        selectinload(Agent.current_version)
    )
    
    # Filter by workspace if specified
    if workspace_id:
        await verify_workspace_access(workspace_id, current_user, db)
        query = query.where(Agent.workspace_id == workspace_id)
    else:
        # Get all workspaces user has access to
        if not current_user.is_superuser:
            workspace_query = select(WorkspaceMember.workspace_id).where(
                WorkspaceMember.user_id == current_user.id
            )
            workspace_ids = await db.execute(workspace_query)
            accessible_workspaces = [w[0] for w in workspace_ids]
            query = query.where(Agent.workspace_id.in_(accessible_workspaces))
    
    # Apply filters
    if type:
        query = query.where(Agent.type == type)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Agent.name.ilike(search_pattern)) |
            (Agent.description.ilike(search_pattern))
        )
    
    if tags:
        # Filter agents that have all specified tags
        for tag in tags:
            query = query.where(Agent.tags.contains([tag]))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query)
    
    # Apply cursor pagination
    if cursor:
        cursor_id = cursor
        if sort_direction == SortDirection.DESC:
            query = query.where(Agent.id < cursor_id)
        else:
            query = query.where(Agent.id > cursor_id)
    
    # Apply sorting
    order_field = getattr(Agent, sort_by)
    if sort_direction == SortDirection.DESC:
        query = query.order_by(order_field.desc())
    else:
        query = query.order_by(order_field.asc())
    
    # Apply limit
    query = query.limit(limit + 1)
    
    # Execute query
    result = await db.execute(query)
    agents = result.scalars().all()
    
    # Determine pagination info
    has_next = len(agents) > limit
    if has_next:
        agents = agents[:-1]
    
    return AgentListResponse(
        data=[AgentResponse.model_validate(agent) for agent in agents],
        pagination={
            "has_next": has_next,
            "has_previous": cursor is not None,
            "next_cursor": str(agents[-1].id) if has_next and agents else None,
            "total_count": total_count
        }
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> AgentResponse:
    """
    Get a specific agent by ID.
    
    Requires: agents:read permission and workspace access
    """
    require_permissions(current_user, ["agents:read"])
    
    # Get agent
    result = await db.execute(
        select(Agent).options(
            selectinload(Agent.workspace),
            selectinload(Agent.created_by),
            selectinload(Agent.current_version),
            selectinload(Agent.versions)
        ).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify workspace access
    await verify_workspace_access(agent.workspace_id, current_user, db)
    
    return AgentResponse.model_validate(agent)


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    agent_data: AgentCreate
) -> AgentResponse:
    """
    Create a new AI agent.
    
    Requires: agents:write permission and workspace membership
    """
    require_permissions(current_user, ["agents:write"])
    
    # Verify workspace access
    workspace = await verify_workspace_access(
        agent_data.workspace_id,
        current_user,
        db
    )
    
    # Create agent
    agent = Agent(
        name=agent_data.name,
        description=agent_data.description,
        type=agent_data.type,
        workspace_id=agent_data.workspace_id,
        created_by_id=current_user.id,
        config=agent_data.config,
        capabilities=agent_data.capabilities or [],
        tags=agent_data.tags or []
    )
    
    # Create initial version
    initial_version = AgentVersion(
        agent=agent,
        version="1.0.0",
        config=agent_data.config,
        changelog="Initial version",
        created_by_id=current_user.id
    )
    agent.versions.append(initial_version)
    agent.current_version = initial_version
    
    db.add(agent)
    await db.commit()
    await db.refresh(agent, ["workspace", "created_by", "current_version"])
    
    logger.info(
        "agent_created",
        agent_id=str(agent.id),
        workspace_id=agent_data.workspace_id,
        created_by=str(current_user.id)
    )
    
    return AgentResponse.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_update: AgentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> AgentResponse:
    """
    Update an agent.
    
    Requires: agents:write permission and workspace membership
    """
    require_permissions(current_user, ["agents:write"])
    
    # Get agent
    result = await db.execute(
        select(Agent).options(
            selectinload(Agent.current_version)
        ).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify workspace access
    await verify_workspace_access(agent.workspace_id, current_user, db)
    
    # Apply updates
    update_data = agent_update.model_dump(exclude_unset=True)
    
    # Handle config updates - create new version if config changed
    if "config" in update_data:
        new_config = update_data.pop("config")
        if new_config != agent.config:
            # Create new version
            current_version = agent.current_version.version
            version_parts = current_version.split(".")
            version_parts[1] = str(int(version_parts[1]) + 1)  # Increment minor version
            new_version_number = ".".join(version_parts)
            
            new_version = AgentVersion(
                agent_id=agent.id,
                version=new_version_number,
                config=new_config,
                changelog=agent_update.version_changelog or "Configuration updated",
                created_by_id=current_user.id
            )
            
            db.add(new_version)
            agent.current_version = new_version
            agent.config = new_config
    
    # Apply other updates
    for field, value in update_data.items():
        if field != "version_changelog":
            setattr(agent, field, value)
    
    agent.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(agent, ["workspace", "created_by", "current_version"])
    
    logger.info(
        "agent_updated",
        agent_id=agent_id,
        updated_by=str(current_user.id),
        fields=list(update_data.keys())
    )
    
    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Delete an agent.
    
    Requires: agents:delete permission and workspace admin role
    """
    require_permissions(current_user, ["agents:delete"])
    
    # Get agent
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify workspace access with admin requirement
    await verify_workspace_access(
        agent.workspace_id,
        current_user,
        db,
        required_role="admin"
    )
    
    # Soft delete
    agent.is_deleted = True
    await db.commit()
    
    logger.info(
        "agent_deleted",
        agent_id=agent_id,
        deleted_by=str(current_user.id)
    )


# Agent version management

@router.get("/{agent_id}/versions", response_model=List[AgentVersionResponse])
async def list_agent_versions(
    agent_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> List[AgentVersionResponse]:
    """
    List all versions of an agent.
    
    Requires: agents:read permission
    """
    require_permissions(current_user, ["agents:read"])
    
    # Get agent
    result = await db.execute(
        select(Agent).options(
            selectinload(Agent.versions).selectinload(AgentVersion.created_by)
        ).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify workspace access
    await verify_workspace_access(agent.workspace_id, current_user, db)
    
    # Sort versions by creation date descending
    versions = sorted(agent.versions, key=lambda v: v.created_at, reverse=True)
    
    return [AgentVersionResponse.model_validate(v) for v in versions]


@router.post("/{agent_id}/versions/{version_id}/activate", response_model=AgentResponse)
async def activate_agent_version(
    agent_id: str,
    version_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> AgentResponse:
    """
    Activate a specific version of an agent.
    
    Requires: agents:write permission
    """
    require_permissions(current_user, ["agents:write"])
    
    # Get agent and version
    result = await db.execute(
        select(Agent).options(
            selectinload(Agent.versions)
        ).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify workspace access
    await verify_workspace_access(agent.workspace_id, current_user, db)
    
    # Find version
    version = next((v for v in agent.versions if str(v.id) == version_id), None)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    # Activate version
    agent.current_version = version
    agent.config = version.config
    
    await db.commit()
    await db.refresh(agent, ["workspace", "created_by", "current_version"])
    
    logger.info(
        "agent_version_activated",
        agent_id=agent_id,
        version_id=version_id,
        activated_by=str(current_user.id)
    )
    
    return AgentResponse.model_validate(agent)


# Agent execution

@router.post("/{agent_id}/execute", response_model=AgentExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_agent(
    agent_id: str,
    execution_data: AgentExecutionCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> AgentExecutionResponse:
    """
    Execute an agent asynchronously.
    
    Requires: agents:execute permission
    """
    with tracer.start_as_current_span("execute_agent") as span:
        span.set_attribute("agent.id", agent_id)
        span.set_attribute("user.id", str(current_user.id))
        
        require_permissions(current_user, ["agents:execute"])
        
        # Get agent
        result = await db.execute(
            select(Agent).options(
                selectinload(Agent.current_version)
            ).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Verify workspace access
        await verify_workspace_access(agent.workspace_id, current_user, db)
        
        # Create execution record
        execution = AgentExecution(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            agent_version_id=agent.current_version_id,
            user_id=current_user.id,
            input_data=execution_data.input_data,
            parameters=execution_data.parameters or {},
            status=ExecutionStatus.PENDING
        )
        
        db.add(execution)
        await db.commit()
        
        # Schedule background execution
        executor_service = AgentExecutorService()
        background_tasks.add_task(
            executor_service.execute_agent,
            execution_id=execution.id,
            agent=agent,
            input_data=execution_data.input_data,
            parameters=execution_data.parameters
        )
        
        logger.info(
            "agent_execution_started",
            execution_id=execution.id,
            agent_id=agent_id,
            user_id=str(current_user.id)
        )
        
        return AgentExecutionResponse.model_validate(execution)


@router.get("/{agent_id}/executions", response_model=List[AgentExecutionResponse])
async def list_agent_executions(
    agent_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    status: Annotated[Optional[ExecutionStatus], Query()] = None
) -> List[AgentExecutionResponse]:
    """
    List executions of an agent.
    
    Requires: agents:read permission
    """
    require_permissions(current_user, ["agents:read"])
    
    # Get agent to verify access
    agent_result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = agent_result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify workspace access
    await verify_workspace_access(agent.workspace_id, current_user, db)
    
    # Build query
    query = select(AgentExecution).where(
        AgentExecution.agent_id == agent_id
    ).order_by(AgentExecution.started_at.desc()).limit(limit)
    
    if status:
        query = query.where(AgentExecution.status == status)
    
    # Non-superusers can only see their own executions
    if not current_user.is_superuser:
        query = query.where(AgentExecution.user_id == current_user.id)
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    return [AgentExecutionResponse.model_validate(e) for e in executions]


@router.get("/executions/{execution_id}", response_model=AgentExecutionResponse)
async def get_execution(
    execution_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> AgentExecutionResponse:
    """
    Get details of a specific execution.
    
    Requires: agents:read permission
    """
    require_permissions(current_user, ["agents:read"])
    
    # Get execution
    result = await db.execute(
        select(AgentExecution).options(
            selectinload(AgentExecution.agent)
        ).where(AgentExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    # Verify access
    if not current_user.is_superuser and execution.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return AgentExecutionResponse.model_validate(execution)