"""
Integration tests for login flow.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


class TestLoginFlow:
    """Test complete login flow integration."""

    @pytest.mark.asyncio
    @patch('src.core.auth.GoogleOAuth.verify_access_token')
    def test_complete_login_flow(self, mock_verify_token, test_client, mock_google_user_info):
        """Test complete login flow from Google OAuth to session creation."""
        # Mock Google token verification
        mock_verify_token.return_value = mock_google_user_info
        
        # Test login
        login_data = {
            "access_token": "test-google-access-token",
            "provider": "google"
        }
        
        response = test_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["name"] == "Test User"

    def test_auth_status_unauthenticated(self, test_client):
        """Test authentication status for unauthenticated user."""
        response = test_client.get("/api/auth/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_authenticated"] is False
        assert data["user"] is None

    @patch('src.core.auth.GoogleOAuth.verify_access_token')
    def test_auth_status_authenticated(self, mock_verify_token, test_client, mock_google_user_info):
        """Test authentication status for authenticated user."""
        # Mock Google token verification
        mock_verify_token.return_value = mock_google_user_info
        
        # Login first
        login_data = {
            "access_token": "test-google-access-token",
            "provider": "google"
        }
        login_response = test_client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        # Get auth status
        response = test_client.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_authenticated"] is True
        assert data["user"]["email"] == "test@example.com"

    def test_logout(self, test_client):
        """Test logout functionality."""
        response = test_client.post("/api/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Logged out successfully"

    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "version" in data

    @patch('src.core.auth.GoogleOAuth.verify_access_token')
    def test_invalid_google_token(self, mock_verify_token, test_client):
        """Test login with invalid Google token."""
        # Mock Google token verification to raise exception
        mock_verify_token.side_effect = Exception("Invalid token")
        
        login_data = {
            "access_token": "invalid-google-token",
            "provider": "google"
        }
        
        response = test_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 500  # Internal server error due to exception handling

    def test_login_missing_access_token(self, test_client):
        """Test login without access token."""
        login_data = {
            "provider": "google"
        }
        
        response = test_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 422  # Validation error