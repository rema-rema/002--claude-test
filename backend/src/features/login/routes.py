"""
Login feature API routes.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, Cookie, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.core.database import get_db
from src.core.auth import jwt_manager
from .services import auth_service
from .schemas import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    AuthStatus,
    ErrorResponse,
    UserResponse
)

# Create router
auth_router = APIRouter()


@auth_router.post("/login")
async def login(
    request: LoginRequest,
    req: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Google OAuth login endpoint with HTTPOnly Cookie security.
    
    Validates Google access token and creates/updates user session.
    """
    try:
        # Get client info
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        
        # Authenticate with Google
        token_response = await auth_service.authenticate_with_google(
            db=db,
            access_token=request.access_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Set HTTPOnly Cookies for security
        response.set_cookie(
            key="access_token",
            value=token_response.access_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=1800  # 30 minutes
        )
        
        response.set_cookie(
            key="refresh_token", 
            value=token_response.refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=86400  # 1 day
        )
        
        # Return user info without tokens (tokens are now in secure cookies)
        return {
            "success": True,
            "user": token_response.user,
            "message": "Login successful"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh JWT access token using refresh token.
    """
    try:
        token_response = await auth_service.refresh_access_token(
            db=db,
            refresh_token=request.refresh_token
        )
        return token_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@auth_router.post("/logout")
async def logout(
    request: Optional[LogoutRequest] = None,
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user and invalidate session.
    """
    try:
        if access_token:
            # Get session and invalidate it
            session = await auth_service.session_service.get_session_by_token(
                db, access_token
            )
            if session:
                await auth_service.session_service.invalidate_session(
                    db, session.id
                )
        
        response = JSONResponse(
            content={"message": "Logged out successfully"},
            status_code=status.HTTP_200_OK
        )
        
        # Clear cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


async def get_current_user_dependency(
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[UserResponse]:
    """Dependency to get current authenticated user."""
    if not access_token:
        return None
    
    try:
        # Verify token
        payload = jwt_manager.verify_token(access_token)
        user_id = uuid.UUID(payload["sub"])
        
        # Get user
        user = await auth_service.user_service.get_user_by_id(db, user_id)
        if user:
            return UserResponse.model_validate(user)
        return None
        
    except Exception:
        return None


@auth_router.get("/me", response_model=AuthStatus)
async def get_current_user(
    current_user: Optional[UserResponse] = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user information.
    """
    if not current_user:
        return AuthStatus(
            is_authenticated=False,
            user=None,
            session=None
        )
    
    return AuthStatus(
        is_authenticated=True,
        user=current_user,
        session=None  # Session info could be added if needed
    )


@auth_router.get("/status", response_model=AuthStatus)
async def auth_status(
    current_user: Optional[UserResponse] = Depends(get_current_user_dependency)
):
    """
    Check authentication status without requiring login.
    """
    return AuthStatus(
        is_authenticated=current_user is not None,
        user=current_user,
        session=None
    )