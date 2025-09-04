"""
Application configuration using pydantic-settings for type safety and validation.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    """Application settings with pydantic validation."""
    
    # Application
    APP_NAME: str = Field(default="002 Claude Test Backend")
    DEBUG: bool = Field(default=False)
    
    # Mock Auth (Google OAuth を後で追加)
    MOCK_AUTH_ENABLED: bool = Field(default=True, description="Enable mock authentication for development")
    
    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://test_user:test_password@localhost:5432/test_db")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="test_db")
    POSTGRES_USER: str = Field(default="test_user")
    POSTGRES_PASSWORD: str = Field(default="test_password")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379")
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    
    # JWT
    JWT_SECRET: str = Field(default="your_super_secret_jwt_key_change_this_in_production")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    JWT_ALGORITHM: str = Field(default="HS256")
    
    # Google OAuth (後で設定)
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:3001/auth/callback")
    
    # CORS
    CORS_ORIGINS_STR: Optional[str] = Field(default=None, alias='CORS_ORIGINS')
    CORS_ORIGINS: List[str] = []
    
    @validator('CORS_ORIGINS', pre=True, always=True)
    def parse_cors_origins(cls, v, values):
        cors_str = values.get('CORS_ORIGINS_STR')
        if cors_str:
            return [origin.strip() for origin in cors_str.split(',')]
        return ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000", "http://localhost:8001"]
    
    # Server
    BACKEND_PORT: int = Field(default=8001)
    FRONTEND_PORT: int = Field(default=3001)
    
    # Security
    SECRET_KEY: str = Field(default="your_secret_key_for_general_encryption")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()