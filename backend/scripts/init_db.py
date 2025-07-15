"""
Initialize database with default data.
"""

import asyncio
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.core.database import engine, AsyncSessionLocal
from backend.src.core.security import get_password_hash
from backend.src.models.base import Base
from backend.src.models.user import User, Organization, Role, Permission
from backend.src.core.logging import setup_logging, get_logger

logger = get_logger(__name__)


async def create_default_roles_and_permissions(session: AsyncSession) -> None:
    """Create default roles and permissions."""
    # Create permissions
    permissions = [
        # Stories
        {"name": "stories.create", "display_name": "Create Stories", "resource": "stories", "action": "create"},
        {"name": "stories.read", "display_name": "Read Stories", "resource": "stories", "action": "read"},
        {"name": "stories.edit", "display_name": "Edit Stories", "resource": "stories", "action": "edit"},
        {"name": "stories.delete", "display_name": "Delete Stories", "resource": "stories", "action": "delete"},
        # Documents
        {"name": "documents.create", "display_name": "Create Documents", "resource": "documents", "action": "create"},
        {"name": "documents.read", "display_name": "Read Documents", "resource": "documents", "action": "read"},
        {"name": "documents.edit", "display_name": "Edit Documents", "resource": "documents", "action": "edit"},
        {"name": "documents.delete", "display_name": "Delete Documents", "resource": "documents", "action": "delete"},
        # Analytics
        {"name": "analytics.view", "display_name": "View Analytics", "resource": "analytics", "action": "view"},
        # Users
        {"name": "users.manage", "display_name": "Manage Users", "resource": "users", "action": "manage"},
        # Organization
        {"name": "organization.manage", "display_name": "Manage Organization", "resource": "organization", "action": "manage"},
        # Integrations
        {"name": "integrations.manage", "display_name": "Manage Integrations", "resource": "integrations", "action": "manage"},
    ]
    
    created_permissions = []
    for perm_data in permissions:
        permission = Permission(**perm_data)
        session.add(permission)
        created_permissions.append(permission)
    
    await session.flush()
    
    # Create roles
    roles = [
        {
            "name": "admin",
            "display_name": "Administrator",
            "description": "Full system access",
            "is_system": True,
            "permissions": created_permissions  # All permissions
        },
        {
            "name": "product_manager",
            "display_name": "Product Manager",
            "description": "Can manage stories and documents",
            "is_system": True,
            "permissions": [p for p in created_permissions if p.resource in ["stories", "documents", "analytics"]]
        },
        {
            "name": "developer",
            "display_name": "Developer",
            "description": "Can view stories and documents",
            "is_system": True,
            "permissions": [p for p in created_permissions if p.action == "read" or p.resource == "analytics"]
        },
        {
            "name": "viewer",
            "display_name": "Viewer",
            "description": "Read-only access",
            "is_system": True,
            "permissions": [p for p in created_permissions if p.action == "read"]
        }
    ]
    
    for role_data in roles:
        permissions = role_data.pop("permissions")
        role = Role(**role_data)
        role.permissions.extend(permissions)
        session.add(role)
    
    await session.commit()
    logger.info("default_roles_created", count=len(roles))


async def create_demo_organization_and_user(session: AsyncSession) -> None:
    """Create demo organization and admin user."""
    # Create organization
    org = Organization(
        name="Demo Organization",
        slug="demo-org",
        description="Demo organization for testing PRISM",
        tier="free",
        max_users=10,
        max_projects=3,
        max_ai_requests_per_month=1000,
    )
    session.add(org)
    await session.flush()
    
    # Create admin user
    result = await session.execute(select(Role).filter_by(name="admin"))
    admin_role = result.scalar_one()
    
    user = User(
        email="admin@demo.local",
        username="admin",
        password_hash=get_password_hash("admin123"),
        full_name="Demo Admin",
        status="active",
        email_verified=True,
        email_verified_at=datetime.utcnow(),
    )
    user.roles.append(admin_role)
    session.add(user)
    await session.flush()
    
    # Add user to organization
    from backend.src.models.user import UserOrganization
    user_org = UserOrganization(
        user_id=user.id,
        organization_id=org.id,
        role="owner",
        is_primary=True,
    )
    session.add(user_org)
    
    await session.commit()
    logger.info("demo_data_created", org=org.slug, user=user.email)


async def init_db() -> None:
    """Initialize database with default data."""
    setup_logging()
    logger.info("initializing_database")
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_tables_created")
        
        # Create default data
        async with AsyncSessionLocal() as session:
            # Check if already initialized
            result = await session.execute(select(func.count()).select_from(User))
            user_count = result.scalar()
            if user_count > 0:
                logger.info("database_already_initialized")
                return
            
            await create_default_roles_and_permissions(session)
            await create_demo_organization_and_user(session)
        
        logger.info("database_initialization_complete")
        
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())