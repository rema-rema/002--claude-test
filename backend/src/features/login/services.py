"""
Login feature services for user management and authentication.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from src.core.auth import jwt_manager, google_oauth
from src.features.login.models import User, AuthProvider, UserSession
from src.features.login.schemas import (
    UserCreate, UserResponse, AuthProviderCreate,
    TokenResponse, GoogleUserInfo
)


class UserService:
    """User management service."""
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, db: AsyncSession, user_data: UserCreate) -> User:
        """Create new user."""
        user = User(
            id=uuid.uuid4(),
            email=user_data.email,
            name=user_data.name,
            avatar_url=user_data.avatar_url,
            is_active=user_data.is_active,
            profile_data=user_data.profile_data or {},
            preferences={},
            oauth_data=user_data.oauth_data or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError:
            await db.rollback()
            raise ValueError(f"User with email {user_data.email} already exists")
    
    async def update_last_login(self, db: AsyncSession, user_id: uuid.UUID) -> None:
        """Update user's last login timestamp."""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                last_login_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()


class AuthProviderService:
    """OAuth provider management service."""
    
    async def get_provider_by_user_and_provider(
        self, 
        db: AsyncSession, 
        user_id: uuid.UUID, 
        provider: str
    ) -> Optional[AuthProvider]:
        """Get auth provider by user and provider type."""
        result = await db.execute(
            select(AuthProvider).where(
                AuthProvider.user_id == user_id,
                AuthProvider.provider == provider
            )
        )
        return result.scalar_one_or_none()
    
    async def create_auth_provider(
        self, 
        db: AsyncSession, 
        provider_data: AuthProviderCreate
    ) -> AuthProvider:
        """Create new auth provider."""
        auth_provider = AuthProvider(
            id=uuid.uuid4(),
            user_id=provider_data.user_id,
            provider=provider_data.provider,
            provider_user_id=provider_data.provider_user_id,
            access_token=provider_data.access_token,
            refresh_token=provider_data.refresh_token,
            token_expires_at=provider_data.token_expires_at,
            provider_data=provider_data.provider_data or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(auth_provider)
        await db.commit()
        await db.refresh(auth_provider)
        return auth_provider


class SessionService:
    """User session management service."""
    
    async def create_session(
        self, 
        db: AsyncSession, 
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """Create new user session."""
        session_token = jwt_manager.create_access_token({"sub": str(user_id)})
        refresh_token = jwt_manager.create_refresh_token({"sub": str(user_id)})
        
        session = UserSession(
            id=uuid.uuid4(),
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info={},
            is_active=True,
            expires_at=datetime.now(timezone.utc) + timedelta(
                minutes=jwt_manager.access_token_expire_minutes
            ),
            refresh_expires_at=datetime.now(timezone.utc) + timedelta(
                days=jwt_manager.refresh_token_expire_days
            ),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc)
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    
    async def get_session_by_token(
        self, 
        db: AsyncSession, 
        token: str
    ) -> Optional[UserSession]:
        """Get session by token."""
        result = await db.execute(
            select(UserSession).where(
                UserSession.session_token == token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.now(timezone.utc)
            )
        )
        return result.scalar_one_or_none()
    
    async def invalidate_session(self, db: AsyncSession, session_id: uuid.UUID) -> None:
        """Invalidate user session."""
        await db.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(is_active=False)
        )
        await db.commit()
    
    async def cleanup_expired_sessions(self, db: AsyncSession) -> int:
        """Clean up expired sessions."""
        result = await db.execute(
            update(UserSession)
            .where(UserSession.expires_at < datetime.now(timezone.utc))
            .values(is_active=False)
        )
        await db.commit()
        return result.rowcount


class AuthenticationService:
    """Main authentication service."""
    
    def __init__(self):
        self.user_service = UserService()
        self.provider_service = AuthProviderService()
        self.session_service = SessionService()
    
    async def authenticate_with_google(
        self, 
        db: AsyncSession, 
        access_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TokenResponse:
        """Authenticate user with Google OAuth token."""
        
        # Verify Google token and get user info
        google_user_info = await google_oauth.verify_access_token(access_token)
        
        # Check if user exists
        user = await self.user_service.get_user_by_email(
            db, google_user_info["email"]
        )
        
        if not user:
            # Create new user
            user_create = UserCreate(
                email=google_user_info["email"],
                name=google_user_info.get("name", ""),
                avatar_url=google_user_info.get("picture"),
                oauth_data={"google": google_user_info}
            )
            user = await self.user_service.create_user(db, user_create)
            
            # Create auth provider record
            provider_create = AuthProviderCreate(
                user_id=user.id,
                provider="google",
                provider_user_id=google_user_info["id"],
                provider_data=google_user_info
            )
            await self.provider_service.create_auth_provider(db, provider_create)
        
        # Update last login
        await self.user_service.update_last_login(db, user.id)
        
        # Create session
        session = await self.session_service.create_session(
            db, user.id, ip_address, user_agent
        )
        
        # Return token response
        return TokenResponse(
            access_token=session.session_token,
            refresh_token=session.refresh_token,
            expires_in=jwt_manager.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user)
        )
    
    async def refresh_access_token(
        self, 
        db: AsyncSession, 
        refresh_token: str
    ) -> TokenResponse:
        """Refresh access token using refresh token."""
        
        # Verify refresh token
        payload = jwt_manager.verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        
        user_id = uuid.UUID(payload["sub"])
        
        # Get user and create new session
        user = await self.user_service.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Create new session
        session = await self.session_service.create_session(db, user.id)
        
        return TokenResponse(
            access_token=session.session_token,
            refresh_token=session.refresh_token,
            expires_in=jwt_manager.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user)
        )


# Global service instances
auth_service = AuthenticationService()