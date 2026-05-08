import pytest
from fastapi.testclient import TestClient
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
async def test_logout_single_success(client, db_session):
    # Setup: Create a user and a refresh token
    user = User(id="usr_logout", email="logout@example.com", password_hash="hash", name="Logout User")
    db_session.add(user)
    
    token_id = "rtk_logout"
    rt = RefreshToken(
        id=token_id,
        user_id="usr_logout",
        hashed_token="hash", # Opaque for logout check since we only use ID
        expires_at=utc_now() + timedelta(days=30)
    )
    db_session.add(rt)
    await db_session.commit()
    
    # Test Logout
    client.cookies.set("refresh_token", f"{token_id}.secret", domain="testserver", path="/v1/auth")
    response = client.post("/v1/auth/logout")
    
    assert response.status_code == 204
    assert "refresh_token" not in response.cookies or response.cookies["refresh_token"] == ""
    
    # Verify token is marked as used
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.id == token_id))
    revoked_rt = result.scalar_one()
    assert revoked_rt.used_at is not None

@pytest.mark.asyncio
async def test_logout_global_success(client, db_session):
    # Setup: Create a user and TWO refresh tokens
    user = User(id="usr_global", email="global@example.com", password_hash="hash", name="Global User")
    db_session.add(user)
    
    rt1 = RefreshToken(id="rtk1", user_id="usr_global", hashed_token="h", expires_at=utc_now() + timedelta(days=1))
    rt2 = RefreshToken(id="rtk2", user_id="usr_global", hashed_token="h", expires_at=utc_now() + timedelta(days=1))
    db_session.add(rt1)
    db_session.add(rt2)
    await db_session.commit()
    
    # Test Global Logout
    client.cookies.set("refresh_token", "rtk1.secret", domain="testserver", path="/v1/auth")
    response = client.post("/v1/auth/logout", json={"global_logout": True})
    
    assert response.status_code == 204
    
    # Verify BOTH tokens are marked as used
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.user_id == "usr_global"))
    tokens = result.scalars().all()
    assert len(tokens) == 2
    for t in tokens:
        assert t.used_at is not None

@pytest.mark.asyncio
async def test_logout_invalid_token_idempotency(client):
    # Test Logout with missing cookie
    response = client.post("/v1/auth/logout")
    assert response.status_code == 204
    
    # Test Logout with non-existent token
    client.cookies.set("refresh_token", "rtk_none.secret", domain="testserver", path="/v1/auth")
    response = client.post("/v1/auth/logout")
    assert response.status_code == 204
    assert "refresh_token" not in response.cookies or response.cookies["refresh_token"] == ""
