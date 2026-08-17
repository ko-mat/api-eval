import pytest
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_db
from app.models.department import Base
from app.models import employee, history, user
from app.models.user import User
from app.utils.auth import hash_password

# Test database setup (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Sets test environment variables."""
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["STORAGE_BACKEND"] = "local"
    os.environ["LOCAL_STORAGE_DIR"] = "./data/test_photos"
    os.environ["ENCRYPTION_KEY"] = "T5G7Uv5Y9pPq1XJdfk7D7h9kLmNpQrStUvWxYz01234="
    os.environ["JWT_SECRET"] = "super-secret-jwt-key-for-unit-testing-2026"
    os.environ["ADMIN_USERNAME"] = "admin"
    os.environ["ADMIN_PASSWORD"] = "AdminPass2026!"
    yield

@pytest.fixture
async def async_db_session():
    """Provides a transactional database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with TestingSessionLocal() as session:
        # Seed default admin user
        admin = User(
            username="admin",
            hashed_password=hash_password("AdminPass2026!"),
            role="admin",
            is_active=True
        )
        session.add(admin)
        await session.commit()
        
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(async_db_session):
    """Provides an AsyncClient bound to the FastAPI application with mocked database."""
    async def override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()

@pytest.fixture
async def auth_headers(client):
    """Provides an Authorization Bearer header with valid JWT token."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "AdminPass2026!"}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
