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
    def session_maker():
        return db_session
    app.state.db_session_maker = session_maker
    return TestClient(app)

@pytest.mark.asyncio
async def test_refresh_success(client, db_session):
    # Setup: Create a user and a valid refresh token
    from yp_api.application.auth.password_hasher import Argon2PasswordHasher
    hasher = Argon2PasswordHasher()
    
    user = User(id="usr_refresh", email="refresh@example.com", password_hash="hash", name="Refresh User")
    db_session.add(user)
    
    raw_secret = "secret123"
    token_id = "rtk_valid"
    hashed_rt = hasher.hash_password(raw_secret)
    
    rt = RefreshToken(
        id=token_id,
        user_id="usr_refresh",
        hashed_token=hashed_rt,
        expires_at=utc_now() + timedelta(days=30)
    )
    db_session.add(rt)
    await db_session.commit()
    
    # Test Refresh
    client.cookies.set("refresh_token", f"{token_id}.{raw_secret}", domain="testserver", path="/v1/auth")
    response = client.post("/v1/auth/refresh")
    
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
    assert "refresh_token" in response.cookies
    
    # Check that old token is marked as used
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.id == token_id))
    old_rt = result.scalar_one()
    assert old_rt.used_at is not None
    
    # Check that new token exists in DB
    new_token_cookie = response.cookies["refresh_token"]
    new_token_id = new_token_cookie.split(".")[0]
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.id == new_token_id))
    new_rt = result.scalar_one_or_none()
    assert new_rt is not None
    assert new_rt.user_id == "usr_refresh"

@pytest.mark.asyncio
async def test_refresh_token_reuse_detection(client, db_session):
    # Setup: Create a user and TWO refresh tokens, one ALREADY USED
    from yp_api.application.auth.password_hasher import Argon2PasswordHasher
    hasher = Argon2PasswordHasher()
    
    user = User(id="usr_reuse", email="reuse@example.com", password_hash="hash", name="Reuse User")
    db_session.add(user)
    
    # 1. Used token
    used_id = "rtk_used"
    used_secret = "secret_used"
    rt_used = RefreshToken(
        id=used_id,
        user_id="usr_reuse",
        hashed_token=hasher.hash_password(used_secret),
        expires_at=utc_now() + timedelta(days=30),
        used_at=utc_now() - timedelta(minutes=1)
    )
    
    # 2. Another active token for same user
    active_id = "rtk_active"
    rt_active = RefreshToken(
        id=active_id,
        user_id="usr_reuse",
        hashed_token=hasher.hash_password("other"),
        expires_at=utc_now() + timedelta(days=30)
    )
    
    db_session.add(rt_used)
    db_session.add(rt_active)
    await db_session.commit()
    
    # Attempt to REUSE the used token
    client.cookies.set("refresh_token", f"{used_id}.{used_secret}", domain="testserver", path="/v1/auth")
    response = client.post("/v1/auth/refresh")
    
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "token_reuse"
    
    # CRITICAL: Verify that the other active token was ALSO revoked
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.id == active_id))
    revoked_rt = result.scalar_one()
    assert revoked_rt.used_at is not None

@pytest.mark.asyncio
async def test_refresh_token_expired(client, db_session):
    from yp_api.application.auth.password_hasher import Argon2PasswordHasher
    hasher = Argon2PasswordHasher()
    
    user = User(id="usr_expired", email="expired@example.com", password_hash="hash", name="Expired User")
    db_session.add(user)
    
    token_id = "rtk_expired"
    secret = "expired_secret"
    rt = RefreshToken(
        id=token_id,
        user_id="usr_expired",
        hashed_token=hasher.hash_password(secret),
        expires_at=datetime.utcnow() - timedelta(seconds=1)
    )
    db_session.add(rt)
    await db_session.commit()
    
    client.cookies.set("refresh_token", f"{token_id}.{secret}", domain="testserver", path="/v1/auth")
    response = client.post("/v1/auth/refresh")
    
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "invalid_token"
    assert "expired" in response.json()["detail"]["error"]["message"].lower()
