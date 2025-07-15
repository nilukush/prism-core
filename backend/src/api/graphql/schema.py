"""
GraphQL schema definition for PRISM API.
Implements Relay-compliant schema with comprehensive types and operations.
"""

import strawberry
from strawberry import relay
from strawberry.types import Info
from typing import List, Optional, AsyncIterator
from datetime import datetime
import uuid

from backend.src.core.database import get_db
from backend.src.api.deps import get_current_user
from backend.src.models.user import User as UserModel
from backend.src.models.workspace import Workspace as WorkspaceModel
from backend.src.models.agent import Agent as AgentModel
from backend.src.models.organization import Organization as OrganizationModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload


# Enums

@strawberry.enum
class UserRole(str):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


@strawberry.enum
class AgentType(str):
    CONVERSATIONAL = "conversational"
    ANALYTICAL = "analytical"
    AUTOMATION = "automation"
    MONITORING = "monitoring"


@strawberry.enum
class AgentStatus(str):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    ARCHIVED = "archived"


# Node Types

@strawberry.type
class Organization(relay.Node):
    """Organization node type."""
    id: relay.NodeID[str]
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @strawberry.field
    async def workspaces(
        self,
        info: Info,
        first: Optional[int] = 10,
        after: Optional[str] = None
    ) -> relay.Connection["Workspace"]:
        """Get organization's workspaces."""
        db: AsyncSession = info.context["db"]
        # Implementation would paginate workspaces
        return relay.Connection[Workspace](
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None
            ),
            edges=[]
        )


@strawberry.type
class User(relay.Node):
    """User node type."""
    id: relay.NodeID[str]
    email: str
    username: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    @strawberry.field
    async def organization(self, info: Info) -> Optional[Organization]:
        """Get user's organization."""
        db: AsyncSession = info.context["db"]
        user = info.context["current_user"]
        if user.organization:
            return Organization(
                id=str(user.organization.id),
                name=user.organization.name,
                description=user.organization.description,
                created_at=user.organization.created_at,
                updated_at=user.organization.updated_at
            )
        return None
    
    @strawberry.field
    async def workspaces(
        self,
        info: Info,
        first: Optional[int] = 10,
        after: Optional[str] = None
    ) -> relay.Connection["Workspace"]:
        """Get user's accessible workspaces."""
        # Implementation would paginate workspaces
        return relay.Connection[Workspace](
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None
            ),
            edges=[]
        )


@strawberry.type
class Workspace(relay.Node):
    """Workspace node type."""
    id: relay.NodeID[str]
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @strawberry.field
    async def organization(self, info: Info) -> Organization:
        """Get workspace's organization."""
        # Implementation would fetch organization
        pass
    
    @strawberry.field
    async def agents(
        self,
        info: Info,
        first: Optional[int] = 10,
        after: Optional[str] = None,
        type: Optional[AgentType] = None,
        status: Optional[AgentStatus] = None
    ) -> relay.Connection["Agent"]:
        """Get workspace's agents with filtering."""
        # Implementation would paginate and filter agents
        return relay.Connection[Agent](
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None
            ),
            edges=[]
        )
    
    @strawberry.field
    async def members(
        self,
        info: Info,
        first: Optional[int] = 10,
        after: Optional[str] = None
    ) -> relay.Connection["WorkspaceMember"]:
        """Get workspace members."""
        # Implementation would paginate members
        return relay.Connection[WorkspaceMember](
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None
            ),
            edges=[]
        )


@strawberry.type
class WorkspaceMember:
    """Workspace member type."""
    user: User
    role: UserRole
    joined_at: datetime


@strawberry.type
class Agent(relay.Node):
    """AI Agent node type."""
    id: relay.NodeID[str]
    name: str
    description: Optional[str]
    type: AgentType
    status: AgentStatus
    version: str
    capabilities: List[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    
    @strawberry.field
    async def workspace(self, info: Info) -> Workspace:
        """Get agent's workspace."""
        # Implementation would fetch workspace
        pass
    
    @strawberry.field
    async def created_by(self, info: Info) -> User:
        """Get agent creator."""
        # Implementation would fetch creator
        pass
    
    @strawberry.field
    async def executions(
        self,
        info: Info,
        first: Optional[int] = 10,
        after: Optional[str] = None
    ) -> relay.Connection["AgentExecution"]:
        """Get agent executions."""
        # Implementation would paginate executions
        return relay.Connection[AgentExecution](
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None
            ),
            edges=[]
        )


@strawberry.type
class AgentExecution:
    """Agent execution type."""
    id: str
    agent: Agent
    status: str
    input_data: strawberry.scalars.JSON
    output_data: Optional[strawberry.scalars.JSON]
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]


# Input Types

@strawberry.input
class CreateUserInput:
    """Input for creating a user."""
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: str
    organization_id: Optional[str] = None


@strawberry.input
class UpdateUserInput:
    """Input for updating a user."""
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


@strawberry.input
class CreateWorkspaceInput:
    """Input for creating a workspace."""
    name: str
    description: Optional[str] = None
    organization_id: Optional[str] = None


@strawberry.input
class UpdateWorkspaceInput:
    """Input for updating a workspace."""
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[strawberry.scalars.JSON] = None


@strawberry.input
class CreateAgentInput:
    """Input for creating an agent."""
    name: str
    description: Optional[str] = None
    type: AgentType
    workspace_id: str
    config: strawberry.scalars.JSON
    capabilities: Optional[List[str]] = None
    tags: Optional[List[str]] = None


@strawberry.input
class UpdateAgentInput:
    """Input for updating an agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[strawberry.scalars.JSON] = None
    capabilities: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    status: Optional[AgentStatus] = None


@strawberry.input
class ExecuteAgentInput:
    """Input for executing an agent."""
    agent_id: str
    input_data: strawberry.scalars.JSON
    parameters: Optional[strawberry.scalars.JSON] = None


# Payload Types

@strawberry.type
class CreateUserPayload:
    """Payload for user creation."""
    user: Optional[User]
    errors: Optional[List[str]] = None


@strawberry.type
class UpdateUserPayload:
    """Payload for user update."""
    user: Optional[User]
    errors: Optional[List[str]] = None


@strawberry.type
class CreateWorkspacePayload:
    """Payload for workspace creation."""
    workspace: Optional[Workspace]
    errors: Optional[List[str]] = None


@strawberry.type
class UpdateWorkspacePayload:
    """Payload for workspace update."""
    workspace: Optional[Workspace]
    errors: Optional[List[str]] = None


@strawberry.type
class CreateAgentPayload:
    """Payload for agent creation."""
    agent: Optional[Agent]
    errors: Optional[List[str]] = None


@strawberry.type
class UpdateAgentPayload:
    """Payload for agent update."""
    agent: Optional[Agent]
    errors: Optional[List[str]] = None


@strawberry.type
class ExecuteAgentPayload:
    """Payload for agent execution."""
    execution: Optional[AgentExecution]
    errors: Optional[List[str]] = None


# Query Root

@strawberry.type
class Query:
    """Root query type."""
    
    @strawberry.field
    async def viewer(self, info: Info) -> Optional[User]:
        """Get current authenticated user."""
        current_user = info.context.get("current_user")
        if current_user:
            return User(
                id=str(current_user.id),
                email=current_user.email,
                username=current_user.username,
                full_name=current_user.full_name,
                is_active=current_user.is_active,
                is_verified=current_user.is_verified,
                created_at=current_user.created_at,
                updated_at=current_user.updated_at
            )
        return None
    
    @strawberry.field
    async def node(self, id: relay.GlobalID) -> Optional[relay.Node]:
        """Fetch any node by its global ID."""
        # Implementation would resolve node by type and ID
        return None
    
    @strawberry.field
    async def users(
        self,
        info: Info,
        first: Optional[int] = 10,
        after: Optional[str] = None,
        search: Optional[str] = None
    ) -> relay.Connection[User]:
        """List users with pagination and search."""
        # Implementation would check permissions and paginate
        return relay.Connection[User](
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None
            ),
            edges=[]
        )
    
    @strawberry.field
    async def workspaces(
        self,
        info: Info,
        first: Optional[int] = 10,
        after: Optional[str] = None,
        search: Optional[str] = None
    ) -> relay.Connection[Workspace]:
        """List accessible workspaces."""
        # Implementation would check permissions and paginate
        return relay.Connection[Workspace](
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None
            ),
            edges=[]
        )
    
    @strawberry.field
    async def agents(
        self,
        info: Info,
        first: Optional[int] = 10,
        after: Optional[str] = None,
        workspace_id: Optional[str] = None,
        type: Optional[AgentType] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> relay.Connection[Agent]:
        """List agents with filtering."""
        # Implementation would check permissions and paginate
        return relay.Connection[Agent](
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None
            ),
            edges=[]
        )


# Mutation Root

@strawberry.type
class Mutation:
    """Root mutation type."""
    
    @strawberry.mutation
    async def create_user(
        self, info: Info, input: CreateUserInput
    ) -> CreateUserPayload:
        """Create a new user."""
        # Implementation would validate and create user
        return CreateUserPayload(user=None, errors=["Not implemented"])
    
    @strawberry.mutation
    async def update_user(
        self, info: Info, id: str, input: UpdateUserInput
    ) -> UpdateUserPayload:
        """Update an existing user."""
        # Implementation would validate and update user
        return UpdateUserPayload(user=None, errors=["Not implemented"])
    
    @strawberry.mutation
    async def create_workspace(
        self, info: Info, input: CreateWorkspaceInput
    ) -> CreateWorkspacePayload:
        """Create a new workspace."""
        # Implementation would validate and create workspace
        return CreateWorkspacePayload(workspace=None, errors=["Not implemented"])
    
    @strawberry.mutation
    async def update_workspace(
        self, info: Info, id: str, input: UpdateWorkspaceInput
    ) -> UpdateWorkspacePayload:
        """Update an existing workspace."""
        # Implementation would validate and update workspace
        return UpdateWorkspacePayload(workspace=None, errors=["Not implemented"])
    
    @strawberry.mutation
    async def create_agent(
        self, info: Info, input: CreateAgentInput
    ) -> CreateAgentPayload:
        """Create a new AI agent."""
        # Implementation would validate and create agent
        return CreateAgentPayload(agent=None, errors=["Not implemented"])
    
    @strawberry.mutation
    async def update_agent(
        self, info: Info, id: str, input: UpdateAgentInput
    ) -> UpdateAgentPayload:
        """Update an existing agent."""
        # Implementation would validate and update agent
        return UpdateAgentPayload(agent=None, errors=["Not implemented"])
    
    @strawberry.mutation
    async def execute_agent(
        self, info: Info, input: ExecuteAgentInput
    ) -> ExecuteAgentPayload:
        """Execute an AI agent."""
        # Implementation would validate and execute agent
        return ExecuteAgentPayload(execution=None, errors=["Not implemented"])


# Subscription Root

@strawberry.type
class Subscription:
    """Root subscription type."""
    
    @strawberry.subscription
    async def agent_execution_updates(
        self, info: Info, execution_id: str
    ) -> AsyncIterator[AgentExecution]:
        """Subscribe to execution status updates."""
        # Implementation would stream execution updates
        yield AgentExecution(
            id=execution_id,
            agent=None,  # Would be populated
            status="pending",
            input_data={},
            output_data=None,
            error_message=None,
            started_at=datetime.utcnow(),
            completed_at=None,
            duration_ms=None
        )


# Create schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=strawberry.SchemaConfig(
        auto_camel_case=True  # Convert snake_case to camelCase
    )
)