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
async def test_password_reset_flow_success(client, db_session):
    _fake_email_service.sent_emails.clear()
    
    # 1. Setup: Create user and an active session
    from yp_api.application.auth.password_hasher import Argon2PasswordHasher
    hasher = Argon2PasswordHasher()
    
    user = User(
        id="usr_reset", 
        email="reset_me@example.com", 
        password_hash=hasher.hash_password("OldPassword123!"), 
        name="Reset User"
    )
    db_session.add(user)
    
    rt = RefreshToken(id="rtk_to_revoke", user_id="usr_reset", hashed_token="h", expires_at=utc_now() + timedelta(days=1))
    db_session.add(rt)
    await db_session.commit()
    
    # 2. Request Reset
    response = client.post("/v1/auth/password-reset/request", json={"email": "reset_me@example.com"})
    assert response.status_code == 202
    
    # Verify Email
    assert len(_fake_email_service.sent_emails) == 1
    email_data = _fake_email_service.sent_emails[0]
    assert email_data["type"] == "password_reset"
    token = email_data["token"]
    
    # 3. Reset Password
    response = client.post("/v1/auth/password-reset/reset", json={
        "token": token,
        "new_password": "NewStrongPassword123!"
    })
    assert response.status_code == 200
    
    # 4. Verify DB State
    # Refresh user
    result = await db_session.execute(select(User).where(User.id == "usr_reset"))
    updated_user = result.scalar_one()
    assert hasher.verify_password("NewStrongPassword123!", updated_user.password_hash)
    
    # Verify Magic Link is used
    link_id = token.split(".")[0]
    result = await db_session.execute(select(MagicLink).where(MagicLink.id == link_id))
    used_link = result.scalar_one()
    assert used_link.used_at is not None
    
    # Verify Refresh Token is revoked
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.id == "rtk_to_revoke"))
    revoked_rt = result.scalar_one()
    assert revoked_rt.used_at is not None
    
    # Verify Confirmation Email
    assert len(_fake_email_service.sent_emails) == 2
    assert _fake_email_service.sent_emails[1]["type"] == "password_changed"

@pytest.mark.asyncio
async def test_password_reset_request_enumeration_protection(client):
    _fake_email_service.sent_emails.clear()
    
    response = client.post("/v1/auth/password-reset/request", json={"email": "nonexistent@example.com"})
    # Should return 202 even if email doesn't exist
    assert response.status_code == 202
    assert len(_fake_email_service.sent_emails) == 0

@pytest.mark.asyncio
async def test_password_reset_invalid_token(client, db_session):
    response = client.post("/v1/auth/password-reset/reset", json={
        "token": "mgl_wrong.secret",
        "new_password": "NewStrongPassword123!"
    })
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "invalid_reset_token"

@pytest.mark.asyncio
async def test_password_reset_weak_password(client):
    response = client.post("/v1/auth/password-reset/reset", json={
        "token": "mgl_valid.secret",
        "new_password": "weak"
    })
    # Policy validation should happen before token verification or at least fail with validation error
    assert response.status_code == 422
    assert response.json()["detail"]["error"]["code"] == "validation_failed"
