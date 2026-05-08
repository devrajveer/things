import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from yp_api.app_factory import create_app
from yp_api.models.auth import User, RefreshToken
from sqlalchemy import select
from datetime import timedelta
from yp_shared.time import utc_now

@pytest.fixture
def app():
    return create_app()

@pytest.fixture
def client(db_session, app):
    # Mock database session maker
    def session_maker():
        return db_session
    app.state.db_session_maker = session_maker
    
    # Mock Redis for rate limiting
    app.state.redis = AsyncMock()
    app.state.redis.get = AsyncMock(return_value=None)
    app.state.redis.incr = AsyncMock(return_value=1)
    app.state.redis.expire = AsyncMock(return_value=True)
    app.state.redis.delete = AsyncMock(return_value=1)
    
    return TestClient(app)

@pytest.mark.asyncio
async def test_login_success(client, db_session):
    # Setup: Create a user with hashed password
    from yp_api.application.auth.password_hasher import Argon2PasswordHasher
    hasher = Argon2PasswordHasher()
    hashed_password = hasher.hash_password("StrongPassword123!")
    
    user = User(
        id="usr_test_login",
        email="login_test@example.com",
        password_hash=hashed_password,
        name="Login Test User",
        status="active"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Test Login
    response = client.post("/v1/auth/login", json={
        "email": "login_test@example.com",
        "password": "StrongPassword123!"
    })
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["email"] == "login_test@example.com"
    assert "access_token" in data
    assert data["expires_in"] == 900
    
    # Check Cookie (Refresh Token)
    assert "refresh_token" in response.cookies
    
    # Check DB for stored hashed refresh token
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.user_id == "usr_test_login"))
    rt = result.scalar_one_or_none()
    assert rt is not None
    assert rt.hashed_token is not None
    # Verify it's a valid hash
    assert hasher.verify_password(response.cookies["refresh_token"], rt.hashed_token)

@pytest.mark.asyncio
async def test_login_invalid_password(client, db_session):
    # Setup: Create a user
    from yp_api.application.auth.password_hasher import Argon2PasswordHasher
    hasher = Argon2PasswordHasher()
    hashed_password = hasher.hash_password("CorrectPassword123!")
    
    user = User(
        id="usr_wrong_pw",
        email="wrong_pw@example.com",
        password_hash=hashed_password,
        name="Wrong PW User"
    )
    db_session.add(user)
    await db_session.commit()
    
    response = client.post("/v1/auth/login", json={
        "email": "wrong_pw@example.com",
        "password": "WrongPassword123!"
    })
    
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "invalid_credentials"
    
    # Verify rate limit increment was called
    client.app.state.redis.incr.assert_called()

@pytest.mark.asyncio
async def test_login_rate_limited(client):
    # Mock redis to return a high count (already locked)
    client.app.state.redis.get = AsyncMock(return_value="5")
    
    response = client.post("/v1/auth/login", json={
        "email": "locked@example.com",
        "password": "AnyPassword"
    })
    
    assert response.status_code == 429
    assert response.json()["detail"]["error"]["code"] == "rate_limited"
    assert "attempts" in response.json()["detail"]["error"]["message"].lower()

@pytest.mark.asyncio
async def test_login_user_not_found_constant_time(client):
    # This should return 401 but we want to ensure it doesn't leak existence
    response = client.post("/v1/auth/login", json={
        "email": "missing@example.com",
        "password": "SomePassword123!"
    })
    
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "invalid_credentials"
