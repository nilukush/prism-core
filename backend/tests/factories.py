"""
Test factories for generating test data.
Uses factory_boy for consistent and maintainable test data generation.
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice
from faker import Faker
from datetime import datetime, timedelta
import random
import json

from backend.src.models.user import User
from backend.src.models.organization import Organization
from backend.src.models.workspace import Workspace, WorkspaceMember
from backend.src.models.agent import Agent, AgentVersion, AgentExecution
from backend.src.models.prompt import PromptTemplate
# Role imported from user model, Permission
from backend.src.services.auth import AuthService

fake = Faker()


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with common configuration."""
    
    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "commit"


class OrganizationFactory(BaseFactory):
    """Factory for creating Organization instances."""
    
    class Meta:
        model = Organization
    
    name = factory.LazyAttribute(lambda _: fake.company())
    description = factory.LazyAttribute(lambda _: fake.catch_phrase())
    settings = factory.LazyFunction(
        lambda: {
            "max_users": random.randint(10, 1000),
            "max_agents": random.randint(5, 100),
            "features": random.sample(
                ["analytics", "ai_agents", "integrations", "advanced_security"],
                k=random.randint(2, 4)
            ),
            "trial": random.choice([True, False]),
        }
    )


class UserFactory(BaseFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
    
    email = factory.LazyAttribute(lambda _: fake.email())
    username = factory.LazyAttribute(lambda _: fake.user_name())
    full_name = factory.LazyAttribute(lambda _: fake.name())
    is_active = True
    is_verified = factory.LazyAttribute(lambda _: random.choice([True, False]))
    is_superuser = False
    organization = factory.SubFactory(OrganizationFactory)
    organization_id = factory.SelfAttribute("organization.id")
    hashed_password = factory.LazyFunction(
        lambda: AuthService().hash_password("password123!")
    )
    preferences = factory.LazyFunction(
        lambda: {
            "theme": random.choice(["light", "dark", "auto"]),
            "notifications": {
                "email": random.choice([True, False]),
                "in_app": True,
                "digest": random.choice(["daily", "weekly", "never"])
            },
            "language": random.choice(["en", "es", "fr", "de", "ja"]),
        }
    )
    
    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for role in extracted:
                self.roles.append(role)


class RoleFactory(BaseFactory):
    """Factory for creating Role instances."""
    
    class Meta:
        model = Role
    
    name = factory.LazyAttribute(
        lambda _: fake.random_element(["admin", "developer", "viewer", "analyst"])
    )
    description = factory.LazyAttribute(lambda obj: f"Role for {obj.name} users")
    
    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for permission in extracted:
                self.permissions.append(permission)


class PermissionFactory(BaseFactory):
    """Factory for creating Permission instances."""
    
    class Meta:
        model = Permission
    
    name = factory.LazyAttribute(
        lambda _: f"{fake.word()}:{random.choice(['read', 'write', 'delete', 'execute'])}"
    )
    description = factory.LazyAttribute(lambda obj: f"Permission to {obj.name}")


class WorkspaceFactory(BaseFactory):
    """Factory for creating Workspace instances."""
    
    class Meta:
        model = Workspace
    
    name = factory.LazyAttribute(lambda _: f"{fake.company()} Workspace")
    description = factory.LazyAttribute(lambda _: fake.text(max_nb_chars=200))
    organization = factory.SubFactory(OrganizationFactory)
    organization_id = factory.SelfAttribute("organization.id")
    created_by = factory.SubFactory(UserFactory, organization=factory.SelfAttribute("..organization"))
    created_by_id = factory.SelfAttribute("created_by.id")
    settings = factory.LazyFunction(
        lambda: {
            "theme": random.choice(["light", "dark"]),
            "notifications": random.choice([True, False]),
            "auto_save": True,
            "collaboration": {
                "enabled": True,
                "real_time": random.choice([True, False])
            }
        }
    )


class WorkspaceMemberFactory(BaseFactory):
    """Factory for creating WorkspaceMember instances."""
    
    class Meta:
        model = WorkspaceMember
    
    workspace = factory.SubFactory(WorkspaceFactory)
    workspace_id = factory.SelfAttribute("workspace.id")
    user = factory.SubFactory(
        UserFactory,
        organization=factory.SelfAttribute("..workspace.organization")
    )
    user_id = factory.SelfAttribute("user.id")
    role = factory.LazyAttribute(
        lambda _: random.choice(["admin", "member", "viewer"])
    )


class PromptTemplateFactory(BaseFactory):
    """Factory for creating PromptTemplate instances."""
    
    class Meta:
        model = PromptTemplate
    
    name = factory.LazyAttribute(lambda _: f"{fake.word().title()} Assistant")
    description = factory.LazyAttribute(lambda _: fake.sentence())
    content = factory.LazyAttribute(
        lambda _: f"""You are a helpful {fake.job()} assistant.
        
Your task is to {fake.bs()}.

User input: {{user_input}}
Context: {{context}}

Please provide a {fake.word()} response."""
    )
    variables = factory.LazyAttribute(
        lambda obj: ["user_input", "context"]  # Extract from content
    )
    category = factory.LazyAttribute(
        lambda _: random.choice(["support", "development", "analytics", "general"])
    )
    is_public = factory.LazyAttribute(lambda _: random.choice([True, False]))
    created_by = factory.SubFactory(UserFactory)
    created_by_id = factory.SelfAttribute("created_by.id")
    organization = factory.SelfAttribute("created_by.organization")
    organization_id = factory.SelfAttribute("organization.id")


class AgentFactory(BaseFactory):
    """Factory for creating Agent instances."""
    
    class Meta:
        model = Agent
    
    name = factory.LazyAttribute(lambda _: f"{fake.word().title()} Agent")
    description = factory.LazyAttribute(lambda _: fake.text(max_nb_chars=200))
    type = factory.LazyAttribute(
        lambda _: random.choice(["conversational", "analytical", "automation", "monitoring"])
    )
    workspace = factory.SubFactory(WorkspaceFactory)
    workspace_id = factory.SelfAttribute("workspace.id")
    created_by = factory.SubFactory(
        UserFactory,
        organization=factory.SelfAttribute("..workspace.organization")
    )
    created_by_id = factory.SelfAttribute("created_by.id")
    config = factory.LazyFunction(
        lambda: {
            "model": random.choice(["gpt-4", "gpt-3.5-turbo", "claude-2"]),
            "temperature": round(random.uniform(0.1, 1.0), 1),
            "max_tokens": random.choice([500, 1000, 2000]),
            "tools": random.sample(
                ["web_search", "code_analysis", "data_query", "file_access"],
                k=random.randint(1, 3)
            ),
            "memory": {
                "type": random.choice(["conversation", "summary", "none"]),
                "max_messages": random.randint(10, 100)
            }
        }
    )
    capabilities = factory.LazyAttribute(
        lambda obj: random.sample(
            ["conversation", "analysis", "code_generation", "data_processing", "web_search"],
            k=random.randint(2, 4)
        )
    )
    tags = factory.LazyFunction(
        lambda: [fake.word() for _ in range(random.randint(1, 5))]
    )


class AgentVersionFactory(BaseFactory):
    """Factory for creating AgentVersion instances."""
    
    class Meta:
        model = AgentVersion
    
    agent = factory.SubFactory(AgentFactory)
    agent_id = factory.SelfAttribute("agent.id")
    version = factory.LazyAttribute(
        lambda _: f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
    )
    config = factory.SelfAttribute("agent.config")
    changelog = factory.LazyAttribute(lambda _: fake.sentence())
    created_by = factory.SelfAttribute("agent.created_by")
    created_by_id = factory.SelfAttribute("created_by.id")


class AgentExecutionFactory(BaseFactory):
    """Factory for creating AgentExecution instances."""
    
    class Meta:
        model = AgentExecution
    
    agent = factory.SubFactory(AgentFactory)
    agent_id = factory.SelfAttribute("agent.id")
    agent_version = factory.SubFactory(AgentVersionFactory, agent=factory.SelfAttribute("..agent"))
    agent_version_id = factory.SelfAttribute("agent_version.id")
    user = factory.SubFactory(
        UserFactory,
        organization=factory.SelfAttribute("..agent.workspace.organization")
    )
    user_id = factory.SelfAttribute("user.id")
    input_data = factory.LazyFunction(
        lambda: {
            "message": fake.sentence(),
            "context": {
                "session_id": fake.uuid4(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
    parameters = factory.LazyFunction(
        lambda: {
            "temperature": round(random.uniform(0.1, 1.0), 1),
            "max_tokens": random.choice([100, 500, 1000])
        }
    )
    status = factory.LazyAttribute(
        lambda _: random.choice(["pending", "running", "completed", "failed"])
    )
    
    @factory.lazy_attribute
    def output_data(self):
        if self.status == "completed":
            return {
                "response": fake.text(),
                "confidence": round(random.uniform(0.7, 1.0), 2),
                "tokens_used": random.randint(50, 500)
            }
        return None
    
    @factory.lazy_attribute
    def error_message(self):
        if self.status == "failed":
            return random.choice([
                "Model API timeout",
                "Invalid input format",
                "Rate limit exceeded",
                "Internal processing error"
            ])
        return None
    
    @factory.lazy_attribute
    def started_at(self):
        if self.status != "pending":
            return datetime.utcnow() - timedelta(minutes=random.randint(1, 60))
        return None
    
    @factory.lazy_attribute
    def completed_at(self):
        if self.status in ["completed", "failed"] and self.started_at:
            return self.started_at + timedelta(seconds=random.randint(1, 120))
        return None
    
    @factory.lazy_attribute
    def metrics(self):
        if self.status == "completed":
            return {
                "tokens_used": random.randint(100, 1000),
                "latency_ms": random.randint(100, 5000),
                "model_time_ms": random.randint(50, 4000),
                "memory_mb": round(random.uniform(50, 200), 1)
            }
        return {}


# Batch creation helpers

def create_test_organization_with_users(session, num_users=5):
    """Create an organization with multiple users."""
    org = OrganizationFactory.create(session=session)
    users = UserFactory.create_batch(num_users, organization=org, session=session)
    return org, users


def create_workspace_with_members(session, organization, users, num_agents=3):
    """Create a workspace with members and agents."""
    workspace = WorkspaceFactory.create(
        organization=organization,
        created_by=users[0],
        session=session
    )
    
    # Add members
    for user in users:
        WorkspaceMemberFactory.create(
            workspace=workspace,
            user=user,
            role="admin" if user == users[0] else "member",
            session=session
        )
    
    # Create agents
    agents = AgentFactory.create_batch(
        num_agents,
        workspace=workspace,
        created_by=random.choice(users),
        session=session
    )
    
    # Create versions for each agent
    for agent in agents:
        AgentVersionFactory.create(agent=agent, session=session)
    
    return workspace, agents


def create_complete_test_environment(session):
    """Create a complete test environment with all models."""
    # Create permissions and roles
    permissions = PermissionFactory.create_batch(10, session=session)
    admin_role = RoleFactory.create(
        name="admin",
        permissions=permissions,
        session=session
    )
    member_role = RoleFactory.create(
        name="member",
        permissions=permissions[:5],
        session=session
    )
    
    # Create organizations with users
    org1, users1 = create_test_organization_with_users(session, 5)
    org2, users2 = create_test_organization_with_users(session, 3)
    
    # Assign roles
    users1[0].roles.append(admin_role)
    users1[1].roles.append(member_role)
    
    # Create workspaces with agents
    workspace1, agents1 = create_workspace_with_members(session, org1, users1[:3], 5)
    workspace2, agents2 = create_workspace_with_members(session, org1, users1[2:], 3)
    
    # Create prompt templates
    templates = PromptTemplateFactory.create_batch(
        10,
        created_by=factory.LazyFunction(lambda: random.choice(users1)),
        organization=org1,
        session=session
    )
    
    # Create agent executions
    for agent in agents1[:3]:
        AgentExecutionFactory.create_batch(
            random.randint(5, 15),
            agent=agent,
            user=factory.LazyFunction(lambda: random.choice(users1)),
            session=session
        )
    
    return {
        "organizations": [org1, org2],
        "users": users1 + users2,
        "workspaces": [workspace1, workspace2],
        "agents": agents1 + agents2,
        "templates": templates,
        "roles": [admin_role, member_role],
        "permissions": permissions
    }