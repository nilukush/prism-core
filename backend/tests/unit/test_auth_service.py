"""
Unit tests for authentication service.
Tests JWT token generation, validation, and user authentication logic.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import jwt

from backend.src.services.auth import AuthService, TokenBlacklist, RefreshTokenStore
from backend.src.core.config import settings
from backend.src.schemas.auth import TokenType


@pytest.mark.unit
class TestAuthService:
    """Test cases for AuthService."""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance."""
        return AuthService()
    
    def test_hash_password(self, auth_service):
        """Test password hashing."""
        password = "testpassword123!"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60
    
    def test_verify_password(self, auth_service):
        """Test password verification."""
        password = "testpassword123!"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrongpassword", hashed) is False
    
    def test_create_access_token(self, auth_service):
        """Test access token creation."""
        user_id = "test-user-id"
        token = auth_service.create_access_token(user_id=user_id)
        
        # Decode token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == user_id
        assert payload["type"] == TokenType.ACCESS
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    def test_create_refresh_token(self, auth_service):
        """Test refresh token creation."""
        user_id = "test-user-id"
        token_data = auth_service.create_refresh_token(user_id=user_id)
        
        assert "token" in token_data
        assert "family_id" in token_data
        assert "token_id" in token_data
        
        # Decode token
        payload = jwt.decode(
            token_data["token"],
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == user_id
        assert payload["type"] == TokenType.REFRESH
        assert payload["family_id"] == token_data["family_id"]
        assert payload["token_id"] == token_data["token_id"]
    
    def test_decode_token_valid(self, auth_service):
        """Test decoding valid token."""
        user_id = "test-user-id"
        token = auth_service.create_access_token(user_id=user_id)
        
        payload = auth_service.decode_token(token)
        
        assert payload["sub"] == user_id
        assert payload["type"] == TokenType.ACCESS
    
    def test_decode_token_expired(self, auth_service):
        """Test decoding expired token."""
        # Create token with past expiration
        past_time = datetime.utcnow() - timedelta(hours=1)
        token_data = {
            "sub": "test-user-id",
            "type": TokenType.ACCESS,
            "exp": past_time,
            "iat": past_time - timedelta(hours=2),
            "jti": "test-jti"
        }
        
        expired_token = jwt.encode(
            token_data,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        payload = auth_service.decode_token(expired_token)
        assert payload is None
    
    def test_decode_token_invalid(self, auth_service):
        """Test decoding invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = auth_service.decode_token(invalid_token)
        assert payload is None
    
    def test_create_tokens(self, auth_service):
        """Test creating both access and refresh tokens."""
        user_id = "test-user-id"
        tokens = auth_service.create_tokens(user_id=user_id)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert "expires_in" in tokens
        assert tokens["token_type"] == "bearer"
    
    @patch('src.services.auth.TokenBlacklist.is_blacklisted')
    @patch('src.services.auth.RefreshTokenStore.validate_token')
    async def test_validate_refresh_token_success(
        self, mock_validate, mock_blacklist, auth_service
    ):
        """Test successful refresh token validation."""
        mock_blacklist.return_value = False
        mock_validate.return_value = True
        
        token_data = auth_service.create_refresh_token(user_id="test-user-id")
        
        result = await auth_service.validate_refresh_token(token_data["token"])
        
        assert result is not None
        assert result["sub"] == "test-user-id"
        mock_blacklist.assert_called_once()
        mock_validate.assert_called_once()
    
    @patch('src.services.auth.TokenBlacklist.is_blacklisted')
    async def test_validate_refresh_token_blacklisted(
        self, mock_blacklist, auth_service
    ):
        """Test validation of blacklisted refresh token."""
        mock_blacklist.return_value = True
        
        token_data = auth_service.create_refresh_token(user_id="test-user-id")
        
        result = await auth_service.validate_refresh_token(token_data["token"])
        
        assert result is None
        mock_blacklist.assert_called_once()


@pytest.mark.unit
class TestTokenBlacklist:
    """Test cases for TokenBlacklist."""
    
    @pytest.fixture
    def blacklist(self):
        """Create TokenBlacklist instance."""
        return TokenBlacklist()
    
    async def test_add_token(self, blacklist):
        """Test adding token to blacklist."""
        token_id = "test-jti"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        await blacklist.add_token(token_id, expires_at)
        
        # In real implementation, this would check Redis
        # For now, we'll just verify the method runs
        assert True
    
    async def test_is_blacklisted(self, blacklist):
        """Test checking if token is blacklisted."""
        token_id = "test-jti"
        
        # In real implementation, this would check Redis
        result = await blacklist.is_blacklisted(token_id)
        
        # Should return False for non-existent token
        assert result is False
    
    async def test_clear_expired(self, blacklist):
        """Test clearing expired tokens."""
        # In real implementation, this would clear Redis entries
        await blacklist.clear_expired()
        
        # Verify method runs without error
        assert True


@pytest.mark.unit
class TestRefreshTokenStore:
    """Test cases for RefreshTokenStore."""
    
    @pytest.fixture
    def token_store(self):
        """Create RefreshTokenStore instance."""
        return RefreshTokenStore()
    
    def test_create_family(self, token_store):
        """Test creating token family."""
        user_id = "test-user-id"
        family_id, token_id = token_store.create_family(user_id)
        
        assert family_id is not None
        assert token_id is not None
        assert family_id in token_store._families
        assert token_store._families[family_id]["user_id"] == user_id
        assert token_store._families[family_id]["current_token_id"] == token_id
    
    def test_validate_token_success(self, token_store):
        """Test successful token validation."""
        user_id = "test-user-id"
        family_id, token_id = token_store.create_family(user_id)
        
        result = token_store.validate_token(family_id, token_id)
        assert result is True
    
    def test_validate_token_invalid_family(self, token_store):
        """Test validation with invalid family ID."""
        result = token_store.validate_token("invalid-family", "token-id")
        assert result is False
    
    def test_validate_token_wrong_token(self, token_store):
        """Test validation with wrong token ID."""
        user_id = "test-user-id"
        family_id, token_id = token_store.create_family(user_id)
        
        result = token_store.validate_token(family_id, "wrong-token")
        assert result is False
    
    def test_validate_token_reuse_detection(self, token_store):
        """Test token reuse detection."""
        user_id = "test-user-id"
        family_id, token_id = token_store.create_family(user_id)
        
        # Rotate token
        new_token_id = token_store.rotate_token(family_id)
        
        # Try to use old token - should invalidate family
        result = token_store.validate_token(family_id, token_id)
        assert result is False
        assert family_id not in token_store._families
    
    def test_rotate_token(self, token_store):
        """Test token rotation."""
        user_id = "test-user-id"
        family_id, token_id = token_store.create_family(user_id)
        
        new_token_id = token_store.rotate_token(family_id)
        
        assert new_token_id is not None
        assert new_token_id != token_id
        assert token_store._families[family_id]["current_token_id"] == new_token_id
        assert token_id in token_store._families[family_id]["used_tokens"]
    
    def test_invalidate_family(self, token_store):
        """Test family invalidation."""
        user_id = "test-user-id"
        family_id, token_id = token_store.create_family(user_id)
        
        token_store.invalidate_family(family_id)
        
        assert family_id not in token_store._families
    
    def test_invalidate_user_tokens(self, token_store):
        """Test invalidating all user tokens."""
        user_id = "test-user-id"
        
        # Create multiple families
        family1, _ = token_store.create_family(user_id)
        family2, _ = token_store.create_family(user_id)
        family3, _ = token_store.create_family("other-user")
        
        token_store.invalidate_user_tokens(user_id)
        
        assert family1 not in token_store._families
        assert family2 not in token_store._families
        assert family3 in token_store._families  # Other user's token remains