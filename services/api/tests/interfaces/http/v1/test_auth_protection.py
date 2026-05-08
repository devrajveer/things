import pytest
from fastapi.testclient import TestClient
from yp_api.app_factory import create_app
from yp_api.models.auth import User
from yp_api.application.auth.token_service import TokenService

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
async def test_protected_route_unauthorized(client):
    # No token
    response = client.get("/v1/auth/sessions")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_invalid_token(client):
    # Invalid token
    response = client.get("/v1/auth/sessions", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_inactive_user(client, db_session):
    # Setup: Inactive user
    user = User(id="usr_inactive", email="inactive@example.com", password_hash="h", name="Inactive", status="inactive")
    db_session.add(user)
    await db_session.commit()
    
    token_service = TokenService()
    token = token_service.create_access_token("usr_inactive")
    
    response = client.get("/v1/auth/sessions", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "forbidden"

@pytest.mark.asyncio
async def test_protected_route_non_existent_user(client, db_session):
    # Token for non-existent user
    token_service = TokenService()
    token = token_service.create_access_token("usr_not_exists")
    
    response = client.get("/v1/auth/sessions", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "unauthorized"
