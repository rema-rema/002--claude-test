"""
JWT authentication and Google OAuth utilities.
"""
from jose import jwt
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, status

from .simple_config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTManager:
    """JWT token management."""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create refresh token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


class GoogleOAuth:
    """Google OAuth utilities."""
    
    GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
    
    async def verify_access_token(self, access_token: str) -> Dict[str, Any]:
        """Verify Google access token and return user info."""
        async with httpx.AsyncClient() as client:
            # Verify token
            token_response = await client.get(
                self.GOOGLE_TOKEN_INFO_URL,
                params={"access_token": access_token}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google access token"
                )
            
            token_data = token_response.json()
            
            # Verify audience (client ID)
            if token_data.get("aud") != self.client_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token audience mismatch"
                )
            
            # Get user info
            user_response = await client.get(
                self.GOOGLE_USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to get user info from Google"
                )
            
            return user_response.json()
    
    def generate_state_token(self, user_data: Dict[str, Any]) -> str:
        """Generate state token for CSRF protection."""
        state_data = {
            "timestamp": datetime.now(timezone.utc).timestamp(),
            "user_id": user_data.get("id", "")
        }
        return jwt.encode(state_data, settings.SECRET_KEY, algorithm="HS256")
    
    def verify_state_token(self, state_token: str, max_age_minutes: int = 10) -> bool:
        """Verify state token for CSRF protection."""
        try:
            payload = jwt.decode(state_token, settings.SECRET_KEY, algorithms=["HS256"])
            timestamp = payload.get("timestamp")
            if not timestamp:
                return False
            
            # Check if token is not too old
            token_age = datetime.now(timezone.utc).timestamp() - timestamp
            return token_age <= (max_age_minutes * 60)
            
        except jwt.JWTError:
            return False


# Global instances
jwt_manager = JWTManager()
google_oauth = GoogleOAuth()