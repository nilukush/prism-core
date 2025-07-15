"""
Integration tests for user management endpoints.
Tests user CRUD operations, pagination, filtering, and permissions.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.models.user import User
# Role imported from user model, Permission
from tests.factories import UserFactory, RoleFactory, PermissionFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserEndpoints:
    """Test user management API endpoints."""
    
    async def test_list_users_authenticated(
        self, authenticated_client: AsyncClient, test_organization, db_session: AsyncSession
    ):
        """Test listing users with authentication."""
        # Create additional users
        users = UserFactory.create_batch(
            5, 
            organization=test_organization, 
            session=db_session
        )
        await db_session.commit()
        
        response = await authenticated_client.get("/api/v1/users")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) >= 6  # test_user + 5 created
        assert data["pagination"]["total_count"] >= 6
    
    async def test_list_users_pagination(
        self, authenticated_client: AsyncClient, test_organization, db_session: AsyncSession
    ):
        """Test user list pagination."""
        # Create many users
        UserFactory.create_batch(
            20, 
            organization=test_organization, 
            session=db_session
        )
        await db_session.commit()
        
        # First page
        response1 = await authenticated_client.get("/api/v1/users?limit=10")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["data"]) == 10
        assert data1["pagination"]["has_next"] is True
        assert data1["pagination"]["has_previous"] is False
        
        # Second page using cursor
        cursor = data1["pagination"]["next_cursor"]
        response2 = await authenticated_client.get(
            f"/api/v1/users?limit=10&cursor={cursor}"
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["data"]) >= 1
        assert data2["pagination"]["has_previous"] is True
        
        # Ensure different users
        ids1 = {u["id"] for u in data1["data"]}
        ids2 = {u["id"] for u in data2["data"]}
        assert len(ids1.intersection(ids2)) == 0
    
    async def test_list_users_filtering(
        self, authenticated_client: AsyncClient, test_organization, db_session: AsyncSession
    ):
        """Test user list filtering."""
        # Create users with different attributes
        active_users = UserFactory.create_batch(
            3, 
            organization=test_organization,
            is_active=True,
            is_verified=True,
            session=db_session
        )
        inactive_users = UserFactory.create_batch(
            2,
            organization=test_organization,
            is_active=False,
            session=db_session
        )
        await db_session.commit()
        
        # Filter by active status
        response = await authenticated_client.get("/api/v1/users?is_active=true")
        data = response.json()
        assert all(u["is_active"] for u in data["data"])
        
        # Filter by verified status
        response = await authenticated_client.get("/api/v1/users?is_verified=true")
        data = response.json()
        assert all(u["is_verified"] for u in data["data"])
        
        # Search by email
        search_user = active_users[0]
        response = await authenticated_client.get(
            f"/api/v1/users?search={search_user.email[:5]}"
        )
        data = response.json()
        assert len(data["data"]) >= 1
        assert any(u["email"] == search_user.email for u in data["data"])
    
    async def test_list_users_requires_permission(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that listing users requires permission."""
        # Create user without users:read permission
        user = UserFactory.create(session=db_session)
        await db_session.commit()
        
        # Create auth headers
        from src.services.auth import AuthService
        auth_service = AuthService()
        tokens = auth_service.create_tokens(user_id=str(user.id))
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        response = await client.get("/api/v1/users", headers=headers)
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
    
    async def test_get_current_user(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test getting current user profile."""
        response = await authenticated_client.get("/api/v1/users/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert "organization" in data
        assert "roles" in data
        assert "hashed_password" not in data
    
    async def test_get_user_by_id(
        self, authenticated_client: AsyncClient, test_user: User, db_session: AsyncSession
    ):
        """Test getting user by ID."""
        # Create another user
        other_user = UserFactory.create(
            organization_id=test_user.organization_id,
            session=db_session
        )
        await db_session.commit()
        
        response = await authenticated_client.get(f"/api/v1/users/{other_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(other_user.id)
        assert data["email"] == other_user.email
    
    async def test_get_user_different_org(
        self, authenticated_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that users can't see users from other organizations."""
        # Create user in different organization
        other_user = UserFactory.create(session=db_session)
        await db_session.commit()
        
        response = await authenticated_client.get(f"/api/v1/users/{other_user.id}")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    async def test_create_user(
        self, authenticated_client: AsyncClient, test_user: User, db_session: AsyncSession
    ):
        """Test creating a new user."""
        # Give user write permission
        permission = await db_session.execute(
            Permission.__table__.select().where(Permission.name == "users:write")
        )
        perm = permission.scalar_one_or_none()
        if not perm:
            perm = PermissionFactory.create(name="users:write", session=db_session)
            await db_session.commit()
        
        # Add permission to user's role
        role = RoleFactory.create(permissions=[perm], session=db_session)
        test_user.roles.append(role)
        await db_session.commit()
        
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "StrongPassword123!",
            "organization_id": str(test_user.organization_id),
            "is_active": True
        }
        
        response = await authenticated_client.post("/api/v1/users", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["organization"]["id"] == user_data["organization_id"]
    
    async def test_update_user_self(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test user updating their own profile."""
        update_data = {
            "full_name": "Updated Name",
            "username": "updatedusername"
        }
        
        response = await authenticated_client.patch(
            f"/api/v1/users/{test_user.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["username"] == update_data["username"]
    
    async def test_update_user_password(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """Test updating user password."""
        client.headers.update(auth_headers)
        
        update_data = {
            "password": "NewStrongPassword123!"
        }
        
        response = await client.patch(
            f"/api/v1/users/{test_user.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        
        # Verify can login with new password
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "NewStrongPassword123!"
            }
        )
        assert login_response.status_code == 200
    
    async def test_update_user_restricted_fields(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test that regular users can't update restricted fields."""
        update_data = {
            "is_superuser": True,
            "is_verified": True,
            "organization_id": "some-other-org-id"
        }
        
        response = await authenticated_client.patch(
            f"/api/v1/users/{test_user.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        # Restricted fields should not be updated
        assert data["is_superuser"] is False
        assert data["organization"]["id"] == str(test_user.organization_id)
    
    async def test_delete_user(
        self, admin_client: AsyncClient, test_organization, db_session: AsyncSession
    ):
        """Test deleting a user (soft delete)."""
        # Create user to delete
        user_to_delete = UserFactory.create(
            organization=test_organization,
            session=db_session
        )
        await db_session.commit()
        
        response = await admin_client.delete(f"/api/v1/users/{user_to_delete.id}")
        
        assert response.status_code == 204
        
        # Verify user is deactivated
        await db_session.refresh(user_to_delete)
        assert user_to_delete.is_active is False
    
    async def test_delete_user_self_prevented(
        self, authenticated_client: AsyncClient, test_user: User, db_session: AsyncSession
    ):
        """Test that users can't delete themselves."""
        # Give user delete permission
        permission = PermissionFactory.create(name="users:delete", session=db_session)
        role = RoleFactory.create(permissions=[permission], session=db_session)
        test_user.roles.append(role)
        await db_session.commit()
        
        response = await authenticated_client.delete(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["detail"]
    
    async def test_assign_role_to_user(
        self, admin_client: AsyncClient, test_organization, db_session: AsyncSession
    ):
        """Test assigning a role to a user."""
        # Create user and role
        user = UserFactory.create(organization=test_organization, session=db_session)
        role = RoleFactory.create(session=db_session)
        await db_session.commit()
        
        response = await admin_client.post(
            f"/api/v1/users/{user.id}/roles/{role.id}"
        )
        
        assert response.status_code == 204
        
        # Verify role assigned
        await db_session.refresh(user, ["roles"])
        assert role in user.roles
    
    async def test_remove_role_from_user(
        self, admin_client: AsyncClient, test_organization, db_session: AsyncSession
    ):
        """Test removing a role from a user."""
        # Create user with role
        role = RoleFactory.create(session=db_session)
        user = UserFactory.create(
            organization=test_organization,
            roles=[role],
            session=db_session
        )
        await db_session.commit()
        
        response = await admin_client.delete(
            f"/api/v1/users/{user.id}/roles/{role.id}"
        )
        
        assert response.status_code == 204
        
        # Verify role removed
        await db_session.refresh(user, ["roles"])
        assert role not in user.roles