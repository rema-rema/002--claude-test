"""
Pytest configuration and fixtures for login feature tests.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.core.database import Base, get_db
from src.core.config import Settings
from main import app

# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class TestSettings(Settings):
    """Test-specific settings."""
    DATABASE_URL: str = TEST_DATABASE_URL
    JWT_SECRET: str = "test-secret-key"
    GOOGLE_CLIENT_ID: str = "test-google-client-id"
    GOOGLE_CLIENT_SECRET: str = "test-google-client-secret"
    
    class Config:
        env_file = None


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_client(db_session):
    """Create test client with test database."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Test settings fixture."""
    return TestSettings()


@pytest.fixture
def sample_user_data():
    """Sample user data for tests."""
    return {
        "id": "123456789",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
        "verified_email": True,
        "given_name": "Test",
        "family_name": "User",
        "locale": "ja"
    }


@pytest.fixture
def google_token_response():
    """Mock Google token response."""
    return {
        "aud": "test-google-client-id",
        "sub": "123456789",
        "email": "test@example.com",
        "email_verified": "true",
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
        "given_name": "Test",
        "family_name": "User",
        "locale": "ja",
        "iat": 1234567890,
        "exp": 1234571490
    }


@pytest.fixture
def mock_google_user_info():
    """Mock Google user info response."""
    return {
        "id": "123456789",
        "email": "test@example.com",
        "verified_email": True,
        "name": "Test User",
        "given_name": "Test",
        "family_name": "User",
        "picture": "https://example.com/avatar.jpg",
        "locale": "ja"
    }