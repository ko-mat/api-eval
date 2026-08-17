import pytest

@pytest.mark.asyncio
async def test_auth_login_success(client):
    """Verifies that valid credentials return 200 and a JWT access token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "AdminPass2026!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == "admin"

@pytest.mark.asyncio
async def test_auth_login_invalid_password(client):
    """Verifies that invalid password returns 401 Unauthorized."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "WrongPassword!"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_login_nonexistent_user(client):
    """Verifies that nonexistent user returns 401 Unauthorized."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "ghost_user", "password": "AnyPassword"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_unauthenticated_access_denied(client):
    """Verifies that protected endpoints return 401 without Bearer token."""
    response = await client.get("/api/v1/departments")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_invalid_jwt_token(client):
    """Verifies that forged or broken JWT tokens return 401."""
    response = await client.get(
        "/api/v1/departments",
        headers={"Authorization": "Bearer invalid.fake.token"}
    )
    assert response.status_code == 401
