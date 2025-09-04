"""
Unit tests for authentication functionality.
"""
import pytest
from jose import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from src.core.auth import JWTManager, GoogleOAuth
from src.features.login.services import UserService, AuthenticationService
from src.features.login.models import User
from src.features.login.schemas import UserCreate


class TestJWTManager:
    """Test JWT token management."""

    def test_create_access_token(self, test_settings):
        """Test access token creation."""
        jwt_manager = JWTManager()
        data = {"sub": "test-user-id"}
        
        token = jwt_manager.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token structure
        payload = jwt.decode(
            token, 
            test_settings.JWT_SECRET, 
            algorithms=[test_settings.JWT_ALGORITHM]
        )
        assert payload["sub"] == "test-user-id"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token(self, test_settings):
        """Test refresh token creation."""
        jwt_manager = JWTManager()
        data = {"sub": "test-user-id"}
        
        token = jwt_manager.create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token structure
        payload = jwt.decode(
            token, 
            test_settings.JWT_SECRET, 
            algorithms=[test_settings.JWT_ALGORITHM]
        )
        assert payload["sub"] == "test-user-id"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_verify_valid_token(self, test_settings):
        """Test token verification with valid token."""
        jwt_manager = JWTManager()
        data = {"sub": "test-user-id"}
        token = jwt_manager.create_access_token(data)
        
        payload = jwt_manager.verify_token(token)
        
        assert payload["sub"] == "test-user-id"
        assert payload["type"] == "access"

    def test_verify_invalid_token(self):
        """Test token verification with invalid token."""
        jwt_manager = JWTManager()
        
        with pytest.raises(Exception):  # Should raise HTTPException
            jwt_manager.verify_token("invalid-token")

    def test_verify_expired_token(self, test_settings):
        """Test token verification with expired token."""
        # Create expired token
        data = {
            "sub": "test-user-id",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "type": "access"
        }
        expired_token = jwt.encode(
            data, 
            test_settings.JWT_SECRET, 
            algorithm=test_settings.JWT_ALGORITHM
        )
        
        jwt_manager = JWTManager()
        
        with pytest.raises(Exception):  # Should raise HTTPException
            jwt_manager.verify_token(expired_token)


class TestGoogleOAuth:
    """Test Google OAuth utilities."""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_verify_access_token_success(self, mock_get, google_token_response, mock_google_user_info):
        """Test successful Google token verification."""
        # Mock responses
        mock_get.side_effect = [
            AsyncMock(status_code=200, json=lambda: google_token_response),
            AsyncMock(status_code=200, json=lambda: mock_google_user_info)
        ]
        
        google_oauth = GoogleOAuth()
        
        user_info = await google_oauth.verify_access_token("test-access-token")
        
        assert user_info["email"] == "test@example.com"
        assert user_info["name"] == "Test User"
        assert user_info["id"] == "123456789"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_verify_access_token_invalid(self, mock_get):
        """Test Google token verification with invalid token."""
        mock_get.return_value = AsyncMock(status_code=400)
        
        google_oauth = GoogleOAuth()
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await google_oauth.verify_access_token("invalid-token")

    def test_generate_state_token(self):
        """Test state token generation."""
        google_oauth = GoogleOAuth()
        user_data = {"id": "123456789"}
        
        state_token = google_oauth.generate_state_token(user_data)
        
        assert state_token is not None
        assert isinstance(state_token, str)

    def test_verify_state_token_valid(self):
        """Test valid state token verification."""
        google_oauth = GoogleOAuth()
        user_data = {"id": "123456789"}
        
        state_token = google_oauth.generate_state_token(user_data)
        is_valid = google_oauth.verify_state_token(state_token)
        
        assert is_valid is True

    def test_verify_state_token_invalid(self):
        """Test invalid state token verification."""
        google_oauth = GoogleOAuth()
        
        is_valid = google_oauth.verify_state_token("invalid-token")
        
        assert is_valid is False


class TestUserService:
    """Test user service functionality."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test user creation."""
        user_service = UserService()
        user_data = UserCreate(
            email="test@example.com",
            name="Test User",
            avatar_url="https://example.com/avatar.jpg"
        )
        
        user = await user_service.create_user(db_session, user_data)
        
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session):
        """Test getting user by email."""
        user_service = UserService()
        
        # Create user first
        user_data = UserCreate(
            email="test@example.com",
            name="Test User"
        )
        created_user = await user_service.create_user(db_session, user_data)
        
        # Get user by email
        found_user = await user_service.get_user_by_email(db_session, "test@example.com")
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, db_session):
        """Test getting non-existent user by email."""
        user_service = UserService()
        
        found_user = await user_service.get_user_by_email(db_session, "nonexistent@example.com")
        
        assert found_user is None