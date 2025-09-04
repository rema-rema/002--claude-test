"""
Login feature Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict
import uuid


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    is_active: bool = True
    profile_data: Optional[Dict[str, Any]] = {}
    oauth_data: Optional[Dict[str, Any]] = {}


class UserUpdate(BaseModel):
    """User update schema."""
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None
    profile_data: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """User response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    profile_data: Optional[Dict[str, Any]] = {}
    preferences: Optional[Dict[str, Any]] = {}
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class AuthProviderBase(BaseModel):
    """Base auth provider schema."""
    provider: str
    provider_user_id: str


class AuthProviderCreate(AuthProviderBase):
    """Auth provider creation schema."""
    user_id: uuid.UUID
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    provider_data: Optional[Dict[str, Any]] = {}


class AuthProviderResponse(AuthProviderBase):
    """Auth provider response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    provider_data: Optional[Dict[str, Any]] = {}
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    """Login request schema."""
    access_token: str
    provider: str = "google"


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request schema."""
    refresh_token: Optional[str] = None


class GoogleUserInfo(BaseModel):
    """Google user information schema."""
    id: str
    email: str
    verified_email: bool
    name: str
    given_name: str
    family_name: str
    picture: str
    locale: str


class SessionInfo(BaseModel):
    """Session information schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = {}
    is_active: bool
    expires_at: datetime
    created_at: datetime
    last_accessed_at: datetime


class AuthStatus(BaseModel):
    """Authentication status schema."""
    is_authenticated: bool
    user: Optional[UserResponse] = None
    session: Optional[SessionInfo] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None