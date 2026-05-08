import pytest
from fastapi.testclient import TestClient
from yp_api.app_factory import create_app
from yp_api.models.auth import User, RefreshToken
from sqlalchemy import select
from datetime import timedelta
from yp_shared.time import utc_now
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

@pytest.fixture
def auth_header():
    token_service = TokenService()
    token = token_service.create_access_token("usr_sessions")
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_session_management_flow(client, db_session, auth_header):
    # 1. Setup: Create user and multiple sessions
    user = User(id="usr_sessions", email="sessions@example.com", password_hash="h", name="Session User")
    db_session.add(user)
    
    # Session 1: Active
    rt1 = RefreshToken(id="rtk_active_1", user_id="usr_sessions", hashed_token="h", expires_at=utc_now() + timedelta(days=1))
    # Session 2: Active
    rt2 = RefreshToken(id="rtk_active_2", user_id="usr_sessions", hashed_token="h", expires_at=utc_now() + timedelta(days=1))
    # Session 3: Expired
    rt3 = RefreshToken(id="rtk_expired", user_id="usr_sessions", hashed_token="h", expires_at=utc_now() - timedelta(days=1))
    # Session 4: Another user
    user2 = User(id="usr_other", email="other@example.com", password_hash="h", name="Other")
    db_session.add(user2)
    rt4 = RefreshToken(id="rtk_other", user_id="usr_other", hashed_token="h", expires_at=utc_now() + timedelta(days=1))
    
    db_session.add_all([rt1, rt2, rt3, rt4])
    await db_session.commit()
    
    # 2. List Sessions
    response = client.get("/v1/auth/sessions", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2 # Should only return rt1 and rt2
    session_ids = [s["id"] for s in data]
    assert "rtk_active_1" in session_ids
    assert "rtk_active_2" in session_ids
    assert "rtk_expired" not in session_ids
    assert "rtk_other" not in session_ids
    
    # 3. Revoke Session
    response = client.delete("/v1/auth/sessions/rtk_active_1", headers=auth_header)
    assert response.status_code == 204
    
    # Verify revocation in DB
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.id == "rtk_active_1"))
    revoked_rt = result.scalar_one()
    assert revoked_rt.used_at is not None
    
    # 4. List again
    response = client.get("/v1/auth/sessions", headers=auth_header)
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == "rtk_active_2"

@pytest.mark.asyncio
async def test_revoke_other_user_session_fails(client, db_session, auth_header):
    # rt_other belongs to usr_other
    response = client.delete("/v1/auth/sessions/rtk_other", headers=auth_header)
    # The use case handles this by not finding the token for that user, returning success for idempotency
    # but the token should NOT be marked as used in DB
    assert response.status_code == 204
    
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.id == "rtk_other"))
    token = result.scalar_one()
    assert token.used_at is None
