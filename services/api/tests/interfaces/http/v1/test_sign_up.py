import pytest
from fastapi.testclient import TestClient
from yp_api.app_factory import create_app
from yp_api.interfaces.http.dependencies import _fake_email_service
from sqlalchemy import select

@pytest.fixture
def app():
    return create_app()

@pytest.fixture
def client(db_session, app):
    # We must patch db_session_maker to use our test db_session
    def session_maker():
        return db_session
    app.state.db_session_maker = session_maker
    return TestClient(app)

@pytest.mark.asyncio
async def test_sign_up_success(client, db_session):
    _fake_email_service.sent_emails.clear()
    
    response = client.post("/v1/auth/signup", json={
        "email": "test_signup@example.com",
        "password": "StrongPassword123!",
        "name": "Sign Up Test"
    })
    
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["user"]["email"] == "test_signup@example.com"
    assert data["user"]["name"] == "Sign Up Test"
    assert data["organization"]["name"] == "Personal"
    assert data["project"]["name"] == "My Project"
    assert "access_token" in data["tokens"]
    
    # Assert DB state
    from yp_api.models.auth import User, OrganizationMember
    result = await db_session.execute(select(User).where(User.email == "test_signup@example.com"))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.name == "Sign Up Test"

    # Assert Membership
    result = await db_session.execute(select(OrganizationMember).where(OrganizationMember.user_id == user.id))
    membership = result.scalar_one_or_none()
    assert membership is not None
    assert membership.role == "owner"

    # Assert Email Service
    assert len(_fake_email_service.sent_emails) == 1
    email_data = _fake_email_service.sent_emails[0]
    assert email_data["email"] == "test_signup@example.com"
    assert email_data["type"] == "verification"

@pytest.mark.asyncio
async def test_sign_up_duplicate_email(client, db_session):
    # Setup: Create user first
    client.post("/v1/auth/signup", json={
        "email": "dup@example.com",
        "password": "StrongPassword123!",
        "name": "First"
    })
    
    # Attempt second time
    response = client.post("/v1/auth/signup", json={
        "email": "dup@example.com",
        "password": "StrongPassword123!",
        "name": "Second"
    })
    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "email_taken"

@pytest.mark.asyncio
async def test_sign_up_weak_password(client):
    response = client.post("/v1/auth/signup", json={
        "email": "weak@example.com",
        "password": "weak",
        "name": "Weak"
    })
    assert response.status_code == 422
    assert response.json()["detail"]["error"]["code"] == "validation_failed"
