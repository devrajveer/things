import pytest
from fastapi.testclient import TestClient
from yp_api.app_factory import create_app
from yp_api.models.auth import User, MagicLink, RefreshToken
from yp_api.interfaces.http.dependencies import _fake_email_service
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
async def test_magic_link_flow_success(client, db_session):
    _fake_email_service.sent_emails.clear()
    
    # 1. Setup: Create user
    user = User(
        id="usr_magic", 
        email="magic@example.com", 
        password_hash="hash", 
        name="Magic User",
        status="active"
    )
    db_session.add(user)
    await db_session.commit()
    
    # 2. Request Magic Link
    response = client.post("/v1/auth/magic-link/request", json={"email": "magic@example.com"})
    assert response.status_code == 202
    
    # Verify Email
    assert len(_fake_email_service.sent_emails) == 1
    email_data = _fake_email_service.sent_emails[0]
    assert email_data["type"] == "magic_link_login"
    token = email_data["token"]
    
    # 3. Verify Magic Link
    response = client.get(f"/v1/auth/magic-link/verify?token={token}")
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
    assert "refresh_token" in response.cookies
    
    # 4. Verify DB State
    link_id = token.split(".")[0]
    result = await db_session.execute(select(MagicLink).where(MagicLink.id == link_id))
    used_link = result.scalar_one()
    assert used_link.used_at is not None
    
    # Verify Session Created
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.user_id == "usr_magic"))
    rt = result.scalar_one_or_none()
    assert rt is not None

@pytest.mark.asyncio
async def test_magic_link_invalid_token(client):
    response = client.get("/v1/auth/magic-link/verify?token=mgl_invalid.secret")
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "invalid_magic_link"

@pytest.mark.asyncio
async def test_magic_link_expired(client, db_session):
    from yp_api.application.auth.password_hasher import Argon2PasswordHasher
    hasher = Argon2PasswordHasher()
    
    user = User(id="usr_exp_link", email="exp_link@example.com", password_hash="h", name="Exp", status="active")
    db_session.add(user)
    
    token_id = "mgl_expired"
    secret = "secret"
    link = MagicLink(
        id=token_id,
        email="exp_link@example.com",
        hashed_token=hasher.hash_password(secret),
        purpose="login",
        expires_at=utc_now() - timedelta(seconds=1)
    )
    db_session.add(link)
    await db_session.commit()
    
    response = client.get(f"/v1/auth/magic-link/verify?token={token_id}.{secret}")
    assert response.status_code == 401
    assert "expired" in response.json()["detail"]["error"]["message"].lower()
