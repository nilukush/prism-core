#!/usr/bin/env python3
"""
PRISM Database Seeding Script
Seeds the database with initial development data
"""

import asyncio
import sys
from pathlib import Path

# Add backend source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
from src.models.user import User
from src.models.organization import Organization
from src.models.workspace import Workspace
from src.models.role import Role, Permission
from src.models.agent import Agent, AgentVersion
from src.models.prompt import PromptTemplate
from src.services.auth import AuthService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed_database():
    """Seed database with initial development data."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if data already exists
            result = await session.execute("SELECT COUNT(*) FROM users")
            count = result.scalar()
            if count > 0:
                logger.info("Database already contains data, skipping seed")
                return
            
            logger.info("Starting database seeding...")
            
            # Create permissions
            logger.info("Creating permissions...")
            permissions_data = [
                # User permissions
                ("users:read", "View users"),
                ("users:write", "Create and edit users"),
                ("users:delete", "Delete users"),
                # Agent permissions
                ("agents:read", "View agents"),
                ("agents:write", "Create and edit agents"),
                ("agents:execute", "Execute agents"),
                ("agents:delete", "Delete agents"),
                # Workspace permissions
                ("workspaces:read", "View workspaces"),
                ("workspaces:write", "Create and edit workspaces"),
                ("workspaces:delete", "Delete workspaces"),
                # Analytics permissions
                ("analytics:read", "View analytics"),
                ("analytics:write", "Manage analytics"),
                # Admin permissions
                ("admin:all", "Full administrative access"),
                # Organization permissions
                ("org:manage", "Manage organization settings"),
                ("org:billing", "Manage billing"),
            ]
            
            permissions = []
            for name, desc in permissions_data:
                perm = Permission(name=name, description=desc)
                permissions.append(perm)
                session.add(perm)
            
            await session.flush()
            
            # Create roles
            logger.info("Creating roles...")
            
            # Admin role - all permissions
            admin_role = Role(
                name="admin",
                description="Administrator with full access",
                permissions=permissions
            )
            
            # Developer role - most permissions except admin and delete
            dev_perms = [p for p in permissions if not p.name.startswith("admin") and not p.name.endswith("delete") and not p.name.startswith("org:")]
            developer_role = Role(
                name="developer",
                description="Developer with agent and workspace access",
                permissions=dev_perms
            )
            
            # Viewer role - read only
            viewer_perms = [p for p in permissions if p.name.endswith("read")]
            viewer_role = Role(
                name="viewer",
                description="Read-only access",
                permissions=viewer_perms
            )
            
            session.add_all([admin_role, developer_role, viewer_role])
            await session.flush()
            
            # Create organizations
            logger.info("Creating organizations...")
            
            demo_org = Organization(
                name="Demo Organization",
                description="Demo organization for development and testing",
                settings={
                    "trial": False,
                    "max_users": 100,
                    "max_agents": 50,
                    "features": ["analytics", "ai_agents", "integrations"]
                }
            )
            
            test_org = Organization(
                name="Test Organization",
                description="Organization for testing features",
                settings={
                    "trial": True,
                    "max_users": 10,
                    "max_agents": 5,
                    "features": ["ai_agents"]
                }
            )
            
            session.add_all([demo_org, test_org])
            await session.flush()
            
            # Create users
            logger.info("Creating users...")
            auth_service = AuthService()
            
            # Admin user
            admin_user = User(
                email="admin@prism.local",
                username="admin",
                full_name="Admin User",
                is_active=True,
                is_verified=True,
                is_superuser=True,
                organization_id=demo_org.id,
                roles=[admin_role],
                preferences={
                    "theme": "dark",
                    "notifications": {
                        "email": True,
                        "in_app": True
                    }
                }
            )
            admin_user.hashed_password = auth_service.hash_password("admin123!")
            
            # Developer users
            dev_user = User(
                email="developer@prism.local",
                username="developer",
                full_name="Developer User",
                is_active=True,
                is_verified=True,
                organization_id=demo_org.id,
                roles=[developer_role],
                preferences={
                    "theme": "dark",
                    "notifications": {
                        "email": True,
                        "in_app": True
                    }
                }
            )
            dev_user.hashed_password = auth_service.hash_password("dev123!")
            
            # Another developer
            jane_dev = User(
                email="jane.developer@prism.local",
                username="jane_dev",
                full_name="Jane Developer",
                is_active=True,
                is_verified=True,
                organization_id=demo_org.id,
                roles=[developer_role],
                preferences={
                    "theme": "light",
                    "notifications": {
                        "email": False,
                        "in_app": True
                    }
                }
            )
            jane_dev.hashed_password = auth_service.hash_password("jane123!")
            
            # Viewer user
            viewer_user = User(
                email="viewer@prism.local",
                username="viewer",
                full_name="Viewer User",
                is_active=True,
                is_verified=True,
                organization_id=demo_org.id,
                roles=[viewer_role],
                preferences={
                    "theme": "auto",
                    "notifications": {
                        "email": False,
                        "in_app": True
                    }
                }
            )
            viewer_user.hashed_password = auth_service.hash_password("viewer123!")
            
            # Test org user
            test_user = User(
                email="test@prism.local",
                username="testuser",
                full_name="Test User",
                is_active=True,
                is_verified=True,
                organization_id=test_org.id,
                roles=[developer_role],
                preferences={
                    "theme": "light",
                    "notifications": {
                        "email": True,
                        "in_app": True
                    }
                }
            )
            test_user.hashed_password = auth_service.hash_password("test123!")
            
            session.add_all([admin_user, dev_user, jane_dev, viewer_user, test_user])
            await session.flush()
            
            # Create workspaces
            logger.info("Creating workspaces...")
            
            main_workspace = Workspace(
                name="Main Workspace",
                description="Primary workspace for AI agent development",
                organization_id=demo_org.id,
                created_by_id=admin_user.id,
                settings={
                    "theme": "dark",
                    "notifications": True,
                    "auto_save": True,
                    "collaboration": {
                        "enabled": True,
                        "real_time": True
                    }
                }
            )
            
            dev_workspace = Workspace(
                name="Development Workspace",
                description="Workspace for testing new features",
                organization_id=demo_org.id,
                created_by_id=dev_user.id,
                settings={
                    "theme": "dark",
                    "notifications": True,
                    "auto_save": True,
                    "collaboration": {
                        "enabled": True,
                        "real_time": False
                    }
                }
            )
            
            test_workspace = Workspace(
                name="Test Workspace",
                description="Isolated workspace for testing",
                organization_id=test_org.id,
                created_by_id=test_user.id,
                settings={
                    "theme": "light",
                    "notifications": False,
                    "auto_save": False
                }
            )
            
            session.add_all([main_workspace, dev_workspace, test_workspace])
            await session.flush()
            
            # Create prompt templates
            logger.info("Creating prompt templates...")
            
            customer_support_template = PromptTemplate(
                name="Customer Support Assistant",
                description="Template for customer support AI agents",
                content="""You are a helpful customer support assistant for {company_name}.

Your primary responsibilities:
- Answer customer questions accurately and politely
- Help resolve issues efficiently
- Escalate complex problems when necessary
- Maintain a professional and friendly tone

Customer Query: {query}

Please provide a helpful response.""",
                variables=["company_name", "query"],
                category="support",
                is_public=True,
                created_by_id=admin_user.id,
                organization_id=demo_org.id
            )
            
            code_review_template = PromptTemplate(
                name="Code Review Assistant",
                description="Template for code review AI agents",
                content="""You are an expert code reviewer. Please review the following code:

Language: {language}
Context: {context}

Code to review:
```{language}
{code}
```

Please provide:
1. Overall assessment
2. Potential bugs or issues
3. Performance considerations
4. Best practice suggestions
5. Security concerns (if any)""",
                variables=["language", "context", "code"],
                category="development",
                is_public=True,
                created_by_id=dev_user.id,
                organization_id=demo_org.id
            )
            
            data_analysis_template = PromptTemplate(
                name="Data Analysis Assistant",
                description="Template for data analysis AI agents",
                content="""You are a data analysis expert. 

Dataset Description: {dataset_description}
Analysis Goal: {analysis_goal}

Please provide:
1. Initial data insights
2. Recommended analysis approaches
3. Potential visualizations
4. Key metrics to track
5. Next steps for deeper analysis""",
                variables=["dataset_description", "analysis_goal"],
                category="analytics",
                is_public=False,
                created_by_id=jane_dev.id,
                organization_id=demo_org.id
            )
            
            session.add_all([customer_support_template, code_review_template, data_analysis_template])
            await session.flush()
            
            # Create agents
            logger.info("Creating AI agents...")
            
            # Customer Support Agent
            support_agent = Agent(
                name="Customer Support Bot",
                description="AI agent for handling customer support queries",
                type="conversational",
                workspace_id=main_workspace.id,
                created_by_id=admin_user.id,
                config={
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "system_prompt": customer_support_template.content,
                    "tools": ["knowledge_base", "ticket_system"],
                    "memory": {
                        "type": "conversation",
                        "max_messages": 50
                    }
                },
                capabilities=["conversation", "knowledge_retrieval", "ticket_creation"],
                tags=["support", "customer-service", "production"]
            )
            
            support_agent_v1 = AgentVersion(
                agent_id=support_agent.id,
                version="1.0.0",
                config=support_agent.config,
                changelog="Initial version",
                created_by_id=admin_user.id
            )
            
            # Code Review Agent
            code_agent = Agent(
                name="Code Reviewer",
                description="AI agent for automated code reviews",
                type="analytical",
                workspace_id=dev_workspace.id,
                created_by_id=dev_user.id,
                config={
                    "model": "gpt-4",
                    "temperature": 0.3,
                    "max_tokens": 1000,
                    "system_prompt": code_review_template.content,
                    "tools": ["code_analysis", "security_scan"],
                    "languages": ["python", "javascript", "typescript", "go"]
                },
                capabilities=["code_analysis", "security_review", "best_practices"],
                tags=["development", "code-review", "quality"]
            )
            
            code_agent_v1 = AgentVersion(
                agent_id=code_agent.id,
                version="1.0.0",
                config=code_agent.config,
                changelog="Initial version with Python, JS, TS, and Go support",
                created_by_id=dev_user.id
            )
            
            # Data Analysis Agent
            data_agent = Agent(
                name="Data Analyst",
                description="AI agent for data analysis and insights",
                type="analytical",
                workspace_id=main_workspace.id,
                created_by_id=jane_dev.id,
                config={
                    "model": "gpt-4",
                    "temperature": 0.5,
                    "max_tokens": 800,
                    "system_prompt": data_analysis_template.content,
                    "tools": ["data_query", "visualization", "statistics"],
                    "integrations": ["postgres", "bigquery", "snowflake"]
                },
                capabilities=["data_analysis", "visualization", "reporting"],
                tags=["analytics", "data", "insights"]
            )
            
            data_agent_v1 = AgentVersion(
                agent_id=data_agent.id,
                version="1.0.0",
                config=data_agent.config,
                changelog="Initial version with SQL database support",
                created_by_id=jane_dev.id
            )
            
            session.add_all([
                support_agent, support_agent_v1,
                code_agent, code_agent_v1,
                data_agent, data_agent_v1
            ])
            
            # Commit all changes
            await session.commit()
            
            logger.info("Database seeding completed successfully!")
            logger.info("\nCreated:")
            logger.info(f"  - {len(permissions)} permissions")
            logger.info(f"  - 3 roles (admin, developer, viewer)")
            logger.info(f"  - 2 organizations")
            logger.info(f"  - 5 users")
            logger.info(f"  - 3 workspaces")
            logger.info(f"  - 3 prompt templates")
            logger.info(f"  - 3 AI agents")
            
        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            await session.rollback()
            raise


async def main():
    """Main function."""
    try:
        await seed_database()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())