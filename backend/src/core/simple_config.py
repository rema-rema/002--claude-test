"""
Simple configuration for quick startup without pydantic-settings.
"""
import os
from typing import List

class Settings:
    """Simple settings class."""
    
    def __init__(self):
        # Application
        self.APP_NAME = "002 Claude Test Backend"
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"
        
        # Mock Auth
        self.MOCK_AUTH_ENABLED = True
        
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
        self.POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
        self.POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "test_db")
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "test_user")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "test_password")
        
        # Redis
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
        self.REDIS_DB = int(os.getenv("REDIS_DB", "0"))
        
        # JWT
        self.JWT_SECRET = os.getenv("JWT_SECRET", "your_super_secret_jwt_key_change_this_in_production")
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))  # 月1ログインに変更
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        
        # Google OAuth (後で設定)
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self.GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3001/auth/callback")
        
        # CORS
        cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:8000,http://localhost:8001,http://192.168.1.13:3000,http://192.168.1.13:3001,http://192.168.1.13:3002,http://100.115.216.73:3000,http://100.115.216.73:3001,http://100.115.216.73:3002,http://ubuntu.local:3000,http://ubuntu.local:3001,http://ubuntu.local:3002,http://myapp.local:3000,http://myapp.local:3001,http://myapp.local:3002,http://ubuntu.tailbdc514.ts.net:3000,http://ubuntu.tailbdc514.ts.net:3001,http://ubuntu.tailbdc514.ts.net:3002")
        self.CORS_ORIGINS = [origin.strip() for origin in cors_origins_str.split(",")]
        
        # Server
        self.BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8001"))
        self.FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3001"))
        
        # Security
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_for_general_encryption")


# Create settings instance
settings = Settings()