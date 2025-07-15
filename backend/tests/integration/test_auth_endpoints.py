"""
Integration tests for authentication endpoints.
Tests the complete authentication flow including registration, login, and token refresh.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import jwt

from backend.src.core.config import settings
from backend.src.models.user import User
from backend.src.models.organization import Organization
from tests.factories import UserFactory, OrganizationFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    async def test_register_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful user registration."""
        # Create organization first
        org = OrganizationFactory.create(session=db_session)
        await db_session.commit()
        
        registration_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "StrongPassword123!",
            "organization_id": str(org.id)
        }
        
        response = await client.post(
            "/api/v1/auth/register",
            json=registration_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == registration_data["email"]
        assert data["username"] == registration_data["username"]
        assert data["is_verified"] is False
        assert "id" in data
        assert "hashed_password" not in data
    
    async def test_register_duplicate_email(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test registration with duplicate email."""
        registration_data = {
            "email": test_user.email,
            "username": "newusername",
            "full_name": "Another User",
            "password": "StrongPassword123!",
            "organization_id": str(test_user.organization_id)
        }
        
        response = await client.post(
            "/api/v1/auth/register",
            json=registration_data
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    async def test_register_weak_password(
        self, client: AsyncClient, db_session: AsyncSession, test_organization: Organization
    ):
        """Test registration with weak password."""
        registration_data = {
            "email": "weakpass@example.com",
            "username": "weakpassuser",
            "full_name": "Weak Pass User",
            "password": "weak",  # Too short, no uppercase, no special chars
            "organization_id": str(test_organization.id)
        }
        
        response = await client.post(
            "/api/v1/auth/register",
            json=registration_data
        )
        
        assert response.status_code == 422
        error = response.json()["detail"][0]
        assert error["loc"] == ["body", "password"]
        assert "at least 8 characters" in error["msg"]
    
    async def test_login_success(
        self, client: AsyncClient, test_user: User
    ):
        """Test successful login."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword123!"
        }
        
        response = await client.post(
            "/api/v1/auth/login",
            data=login_data  # OAuth2 uses form data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        # Verify access token
        payload = jwt.decode(
            data["access_token"],
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        assert payload["sub"] == str(test_user.id)
        assert payload["type"] == "access"
    
    async def test_login_invalid_credentials(
        self, client: AsyncClient, test_user: User
    ):
        """Test login with invalid credentials."""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = await client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"
    
    async def test_login_inactive_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test login with inactive user."""
        # Create inactive user
        user = UserFactory.create(is_active=False, session=db_session)
        await db_session.commit()
        
        login_data = {
            "username": user.email,
            "password": "password123!"
        }
        
        response = await client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        assert response.status_code == 401
        assert "Account is disabled" in response.json()["detail"]
    
    async def test_refresh_token_success(
        self, client: AsyncClient, test_user: User
    ):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123!"
            }
        )
        tokens = login_response.json()
        
        # Use refresh token
        refresh_data = {
            "refresh_token": tokens["refresh_token"]
        }
        
        response = await client.post(
            "/api/v1/auth/refresh",
            json=refresh_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != tokens["access_token"]
        assert data["refresh_token"] != tokens["refresh_token"]
    
    async def test_refresh_token_reuse_detection(
        self, client: AsyncClient, test_user: User
    ):
        """Test refresh token reuse detection."""
        # Login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123!"
            }
        )
        tokens = login_response.json()
        
        # First refresh - should succeed
        refresh_data = {"refresh_token": tokens["refresh_token"]}
        response1 = await client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response1.status_code == 200
        new_tokens = response1.json()
        
        # Try to reuse old refresh token - should fail
        response2 = await client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response2.status_code == 401
        
        # New refresh token should also be invalidated
        response3 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_tokens["refresh_token"]}
        )
        assert response3.status_code == 401
    
    async def test_logout_success(
        self, authenticated_client: AsyncClient
    ):
        """Test successful logout."""
        response = await authenticated_client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    async def test_logout_invalidates_token(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """Test that logout invalidates the access token."""
        # First make authenticated request
        client.headers.update(auth_headers)
        me_response = await client.get("/api/v1/users/me")
        assert me_response.status_code == 200
        
        # Logout
        logout_response = await client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200
        
        # Try to use same token - should fail
        me_response2 = await client.get("/api/v1/users/me")
        assert me_response2.status_code == 401
    
    async def test_request_password_reset(
        self, client: AsyncClient, test_user: User
    ):
        """Test password reset request."""
        reset_data = {
            "email": test_user.email
        }
        
        response = await client.post(
            "/api/v1/auth/password-reset/request",
            json=reset_data
        )
        
        assert response.status_code == 200
        assert "email will be sent" in response.json()["message"]
    
    async def test_request_password_reset_nonexistent_email(
        self, client: AsyncClient
    ):
        """Test password reset with non-existent email."""
        reset_data = {
            "email": "nonexistent@example.com"
        }
        
        response = await client.post(
            "/api/v1/auth/password-reset/request",
            json=reset_data
        )
        
        # Should return success to prevent email enumeration
        assert response.status_code == 200
        assert "email will be sent" in response.json()["message"]
    
    async def test_reset_password_with_token(
        self, client: AsyncClient, test_user: User, db_session: AsyncSession
    ):
        """Test password reset with valid token."""
        # Generate reset token (in real app this would be from email)
        from src.services.auth import AuthService
        auth_service = AuthService()
        reset_token = auth_service.create_password_reset_token(str(test_user.id))
        
        reset_data = {
            "token": reset_token,
            "new_password": "NewStrongPassword123!"
        }
        
        response = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json=reset_data
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Password reset successful"
        
        # Verify can login with new password
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "NewStrongPassword123!"
            }
        )
        assert login_response.status_code == 200
    
    async def test_verify_email_with_token(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test email verification with valid token."""
        # Create unverified user
        user = UserFactory.create(is_verified=False, session=db_session)
        await db_session.commit()
        
        # Generate verification token
        from src.services.auth import AuthService
        auth_service = AuthService()
        verify_token = auth_service.create_email_verification_token(str(user.id))
        
        response = await client.post(
            f"/api/v1/auth/verify-email/{verify_token}"
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Email verified successfully"
        
        # Check user is verified
        await db_session.refresh(user)
        assert user.is_verified is True
    
    async def test_change_password(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test password change for authenticated user."""
        change_data = {
            "current_password": "testpassword123!",
            "new_password": "NewStrongPassword123!"
        }
        
        response = await authenticated_client.post(
            "/api/v1/auth/change-password",
            json=change_data
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"
    
    async def test_change_password_wrong_current(
        self, authenticated_client: AsyncClient
    ):
        """Test password change with wrong current password."""
        change_data = {
            "current_password": "wrongpassword",
            "new_password": "NewStrongPassword123!"
        }
        
        response = await authenticated_client.post(
            "/api/v1/auth/change-password",
            json=change_data
        )
        
        assert response.status_code == 401
        assert "Current password is incorrect" in response.json()["detail"]
    
    async def test_resend_verification_email(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test resending verification email."""
        # Create unverified user
        user = UserFactory.create(is_verified=False, session=db_session)
        await db_session.commit()
        
        # Create auth headers for unverified user
        from src.services.auth import AuthService
        auth_service = AuthService()
        tokens = auth_service.create_tokens(user_id=str(user.id))
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        response = await client.post(
            "/api/v1/auth/resend-verification",
            headers=headers
        )
        
        assert response.status_code == 200
        assert "Verification email sent" in response.json()["message"]