"""
Database models package.
Contains all SQLAlchemy models for the application.
"""

from backend.src.models.base import Base, TimestampMixin, SoftDeleteMixin
from backend.src.models.user import User, Role, Permission
from backend.src.models.organization import Organization, OrganizationMember, Team, TeamMember
from backend.src.models.workspace import Workspace, WorkspaceMember
from backend.src.models.agent import Agent, AgentVersion, AgentExecution
from backend.src.models.story import Story, StoryComment, StoryAttachment
from backend.src.models.document import Document, DocumentVersion, DocumentTemplate
from backend.src.models.project import Project, Sprint, Epic
from backend.src.models.integration import Integration, IntegrationConfig

__all__ = [
    # Base
    "Base",
    "TimestampMixin", 
    "SoftDeleteMixin",
    # User
    "User",
    "Role",
    "Permission",
    # Organization
    "Organization",
    "OrganizationMember",
    "Team",
    "TeamMember",
    # Workspace
    "Workspace",
    "WorkspaceMember",
    # Agent
    "Agent",
    "AgentVersion",
    "AgentExecution",
    # Story
    "Story",
    "StoryComment",
    "StoryAttachment",
    # Document
    "Document",
    "DocumentVersion",
    "DocumentTemplate",
    # Project
    "Project",
    "Sprint",
    "Epic",
    # Integration
    "Integration",
    "IntegrationConfig",
]