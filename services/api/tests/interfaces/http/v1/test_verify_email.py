import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import ulid
from yp_api.app_factory import create_app
from yp_api.interfaces.http.dependencies import _fake_email_service
from yp_api.models.auth import User, MagicLink
from yp_api.application.auth.password_hasher import Argon2PasswordHasher
from sqlalchemy import select

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
async def test_verify_email_success(client, db_session):
    # Setup User
    user_id = f"usr_{ulid.new().str.lower()}"
    user = User(id=user_id, email="verify@example.com", password_hash="hash", name="Verify Test", status="active")
    db_session.add(user)
    
    # Setup Token
    link_id = f"mgl_{ulid.new().str.lower()}"
    raw_secret = ulid.new().str
    hasher = Argon2PasswordHasher()
    magic_link = MagicLink(
        id=link_id,
        email="verify@example.com",
        hashed_token=hasher.hash_password(raw_secret),
        purpose="verify_email",
        expires_at=datetime.utcnow() + timedelta(days=1)
    )
    db_session.add(magic_link)
    await db_session.commit()
    
    token_to_send = f"{link_id}.{raw_secret}"
    
    response = client.get(f"/v1/auth/verify-email?token={token_to_send}", follow_redirects=False)
    assert response.status_code == 302
    assert "verified=true" in response.headers["location"]
    
    # Assert DB
    result = await db_session.execute(select(User).where(User.id == user_id))
    fetched_user = result.scalar_one()
    assert fetched_user.email_verified_at is not None

@pytest.mark.asyncio
async def test_verify_email_invalid_token(client):
    response = client.get("/v1/auth/verify-email?token=invalid.token", follow_redirects=False)
    assert response.status_code == 302
    assert "error=invalid_token" in response.headers["location"]

@pytest.mark.asyncio
async def test_resend_verification_email(client, db_session):
    _fake_email_service.sent_emails.clear()
    
    # Setup User
    user_id = f"usr_{ulid.new().str.lower()}"
    user = User(id=user_id, email="resend@example.com", password_hash="hash", name="Resend Test", status="active")
    db_session.add(user)
    
    # Setup an OLD token to bypass rate limit
    magic_link = MagicLink(
        id=f"mgl_{ulid.new().str.lower()}",
        email="resend@example.com",
        hashed_token="hash",
        purpose="verify_email",
        expires_at=datetime.utcnow() + timedelta(days=1),
        created_at=datetime.utcnow() - timedelta(minutes=5)
    )
    db_session.add(magic_link)
    await db_session.commit()
    
    response = client.post("/v1/auth/verify-email/resend", json={"email": "resend@example.com"})
    assert response.status_code == 200
    
    assert len(_fake_email_service.sent_emails) == 1
    
    # Now rate limit should trigger
    response2 = client.post("/v1/auth/verify-email/resend", json={"email": "resend@example.com"})
    assert response2.status_code == 429
