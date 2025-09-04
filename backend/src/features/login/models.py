"""
Login feature database models.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, Boolean, Text, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class User(Base):
    """User model with JSONB for flexible data storage."""
    
    __tablename__ = "users"
    
    # Primary fields
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # JSONB fields for flexible data
    profile_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default={}
    )
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default={}
    )
    oauth_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default={}
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_users_email_active', 'email', 'is_active'),
        Index('idx_users_created_at', 'created_at'),
        Index('idx_users_profile_data', 'profile_data', postgresql_using='gin'),
    )


class AuthProvider(Base):
    """OAuth provider information."""
    
    __tablename__ = "auth_providers"
    
    # Primary fields
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True
    )
    provider: Mapped[str] = mapped_column(String(50))  # 'google', 'github', etc
    provider_user_id: Mapped[str] = mapped_column(String(255))
    
    # Token information (encrypted in production)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Provider-specific data
    provider_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default={}
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Constraints and indexes
    __table_args__ = (
        Index('idx_auth_providers_user_provider', 'user_id', 'provider'),
        Index('idx_auth_providers_provider_user_id', 'provider', 'provider_user_id'),
    )


class UserSession(Base):
    """User session management."""
    
    __tablename__ = "sessions"
    
    # Primary fields
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True
    )
    
    # Session data
    session_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    refresh_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    
    # Session metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default={}
    )
    
    # Status and expiry
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    refresh_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Indexes for cleanup and performance
    __table_args__ = (
        Index('idx_user_sessions_user_active', 'user_id', 'is_active'),
        Index('idx_user_sessions_expires_at', 'expires_at'),
        Index('idx_user_sessions_device_info', 'device_info', postgresql_using='gin'),
    )