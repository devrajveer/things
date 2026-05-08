import pytest
import asyncio
from datetime import datetime
from yp_api.domain.users.entities import User
from yp_api.infrastructure.persistence.users_repo import SQLAlchemyUserRepository

# Assuming a db_session fixture exists in conftest.py that yields an AsyncSession
@pytest.mark.asyncio
async def test_sqlalchemy_user_repo_save_and_get(db_session):
    repo = SQLAlchemyUserRepository(db_session)
    
    user = User(
        id="usr_123",
        email="test@example.com",
        password_hash="hash123",
        name="Test User",
        failed_login_count=0
    )
    
    saved = await repo.save(user)
    assert saved.id == "usr_123"
    
    fetched = await repo.get_by_id("usr_123")
    assert fetched is not None
    assert fetched.email == "test@example.com"
    
    # In real PG this matches due to CITEXT
    fetched_email = await repo.get_by_email("test@example.com")
    assert fetched_email is not None
    assert fetched_email.id == "usr_123"
