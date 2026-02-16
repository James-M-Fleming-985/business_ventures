import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.deps import get_db, get_redis
from app.db.base import Base
from app.main import app

# Test database URL
TEST_DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/test_{settings.POSTGRES_DB}"

# Test Redis URL
TEST_REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Create test database
    engine = create_async_engine(
        TEST_DATABASE_URL.replace(f"/test_{settings.POSTGRES_DB}", f"/{settings.POSTGRES_DB}"),
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS test_{settings.POSTGRES_DB}"))
        await conn.execute(text(f"CREATE DATABASE test_{settings.POSTGRES_DB}"))
    await engine.dispose()

    # Create test engine
    test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    # Cleanup
    await test_engine.dispose()
    engine = create_async_engine(
        TEST_DATABASE_URL.replace(f"/test_{settings.POSTGRES_DB}", f"/{settings.POSTGRES_DB}"),
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS test_{settings.POSTGRES_DB}"))
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def redis_client() -> AsyncGenerator[Redis, None]:
    """Create test Redis client."""
    redis = Redis.from_url(TEST_REDIS_URL, decode_responses=True)
    await redis.flushdb()
    yield redis
    await redis.flushdb()
    await redis.close()


@pytest.fixture(scope="function")
def override_get_db(db_session: AsyncSession):
    """Override database dependency."""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def override_get_redis(redis_client: Redis):
    """Override Redis dependency."""
    async def _override_get_redis():
        yield redis_client
    
    app.dependency_overrides[get_redis] = _override_get_redis
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(override_get_db, override_get_redis) -> TestClient:
    """Create test client with overridden dependencies."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture(scope="function")
async def async_client(override_get_db, override_get_redis) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with overridden dependencies."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPassword123!",
    }


@pytest.fixture
def test_admin_data() -> dict:
    """Sample admin data for testing."""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "password": "AdminPassword123!",
        "is_superuser": True,
    }


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_data: dict):
    """Create test user in database."""
    from app.db.repositories.user import UserRepository
    from app.models.user import UserCreate
    
    user_repo = UserRepository(db_session)
    user_create = UserCreate(**test_user_data)
    user = await user_repo.create(user_create)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession, test_admin_data: dict):
    """Create test admin user in database."""
    from app.db.repositories.user import UserRepository
    from app.models.user import UserCreate
    
    user_repo = UserRepository(db_session)
    user_create = UserCreate(**test_admin_data)
    user = await user_repo.create(user_create)
    return user


@pytest.fixture
def auth_headers(test_user) -> dict:
    """Create authentication headers for test user."""
    from app.core.security import create_access_token
    
    access_token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(test_admin) -> dict:
    """Create authentication headers for admin user."""
    from app.core.security import create_access_token
    
    access_token = create_access_token(subject=str(test_admin.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(autouse=True)
def reset_settings_overrides():
    """Reset any settings overrides after each test."""
    yield
    # Reset any modified settings to their original values
    for attr in dir(settings):
        if not attr.startswith("_"):
            original_value = getattr(settings.__class__, attr, None)
            if original_value is not None:
                setattr(settings, attr, original_value)
