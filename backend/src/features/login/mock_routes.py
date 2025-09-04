"""
Mock authentication routes for development (Google OAuth無しで開発進行).
"""
from datetime import datetime, timedelta
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.auth import jwt_manager
from src.core.simple_config import settings
from .models import User
from .schemas import UserResponse, AuthStatus

# Create mock auth router
mock_auth_router = APIRouter()


class MockLoginRequest(BaseModel):
    """Mock login request schema."""
    email: EmailStr
    password: str


class MockRegisterRequest(BaseModel):
    """Mock registration request schema."""
    email: EmailStr
    password: str
    name: str


# Mock user data (本番環境では使用しない)
MOCK_USERS = {
    "test@example.com": {
        "password": "password123",
        "name": "Test User",
        "id": "550e8400-e29b-41d4-a716-446655440001"
    },
    "admin@example.com": {
        "password": "admin123",
        "name": "Admin User",
        "id": "550e8400-e29b-41d4-a716-446655440002"
    }
}


@mock_auth_router.post("/mock-login")
async def mock_login(
    request: MockLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Mock login endpoint for development without Google OAuth.
    
    テスト用アカウント:
    - test@example.com / password123
    - admin@example.com / admin123
    """
    if not settings.MOCK_AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock authentication is disabled"
        )
    
    # Check mock credentials
    mock_user = MOCK_USERS.get(request.email)
    if not mock_user or mock_user["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create mock user data
    user_id = mock_user["id"]
    user_data = {
        "id": user_id,
        "email": request.email,
        "name": mock_user["name"],
        "picture": f"https://ui-avatars.com/api/?name={mock_user['name'].replace(' ', '+')}&background=random",
        "provider": "mock",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Generate JWT tokens
    access_token = jwt_manager.create_access_token(
        data={"sub": user_id, "email": request.email}
    )
    refresh_token = jwt_manager.create_refresh_token(
        data={"sub": user_id}
    )
    
    # Set HTTPOnly Cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Development用にFalse
        samesite="lax",
        max_age=1800  # 30 minutes
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Development用にFalse
        samesite="lax",
        max_age=2592000  # 30 days (月1ログイン)
    )
    
    return {
        "success": True,
        "user": user_data,
        "message": "Mock login successful"
    }


@mock_auth_router.post("/mock-register")
async def mock_register(
    request: MockRegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Mock registration endpoint for development.
    """
    if not settings.MOCK_AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock authentication is disabled"
        )
    
    # Check if user already exists
    if request.email in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create new mock user
    user_id = str(uuid.uuid4())
    MOCK_USERS[request.email] = {
        "password": request.password,
        "name": request.name,
        "id": user_id
    }
    
    user_data = {
        "id": user_id,
        "email": request.email,
        "name": request.name,
        "picture": f"https://ui-avatars.com/api/?name={request.name.replace(' ', '+')}&background=random",
        "provider": "mock",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Generate JWT tokens
    access_token = jwt_manager.create_access_token(
        data={"sub": user_id, "email": request.email}
    )
    refresh_token = jwt_manager.create_refresh_token(
        data={"sub": user_id}
    )
    
    # Set HTTPOnly Cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=1800
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=2592000  # 30 days (月1ログイン)
    )
    
    return {
        "success": True,
        "user": user_data,
        "message": "Mock registration successful"
    }


@mock_auth_router.get("/mock-users")
async def get_mock_users():
    """
    Get list of available mock users for development.
    """
    if not settings.MOCK_AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock authentication is disabled"
        )
    
    # Return users without passwords
    users = []
    for email, data in MOCK_USERS.items():
        users.append({
            "email": email,
            "name": data["name"],
            "hint": "password: " + data["password"][:3] + "***"
        })
    
    return {
        "mock_auth_enabled": True,
        "users": users,
        "note": "These are test accounts for development only"
    }


async def get_current_mock_user(
    access_token: Optional[str] = Cookie(None)
) -> Optional[dict]:
    """Get current mock authenticated user."""
    if not access_token or not settings.MOCK_AUTH_ENABLED:
        return None
    
    try:
        # Verify token
        payload = jwt_manager.verify_token(access_token)
        user_id = payload["sub"]
        email = payload.get("email")
        
        # Find mock user
        for user_email, user_data in MOCK_USERS.items():
            if user_data["id"] == user_id:
                return {
                    "id": user_id,
                    "email": user_email,
                    "name": user_data["name"],
                    "picture": f"https://ui-avatars.com/api/?name={user_data['name'].replace(' ', '+')}&background=random",
                    "provider": "mock"
                }
        return None
        
    except Exception:
        return None


@mock_auth_router.get("/mock-me")
async def get_mock_current_user(
    current_user: Optional[dict] = Depends(get_current_mock_user)
):
    """Get current mock user information."""
    if not current_user:
        return {
            "is_authenticated": False,
            "user": None,
            "mock_auth": settings.MOCK_AUTH_ENABLED
        }
    
    return {
        "is_authenticated": True,
        "user": current_user,
        "mock_auth": True
    }


@mock_auth_router.post("/mock-logout")
async def mock_logout(response: Response):
    """
    Mock logout endpoint - clears authentication cookies.
    """
    if not settings.MOCK_AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock authentication is disabled"
        )
    
    # Clear access_token cookie
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=0  # Expire immediately
    )
    
    # Clear refresh_token cookie
    response.set_cookie(
        key="refresh_token",
        value="",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=0  # Expire immediately
    )
    
    return {
        "success": True,
        "message": "Logout successful",
        "mock_auth": True
    }