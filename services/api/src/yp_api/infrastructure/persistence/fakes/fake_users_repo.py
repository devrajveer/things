from typing import Optional, Dict
from yp_api.domain.users.entities import User
from yp_api.domain.users.repository import UserRepository

class FakeUserRepository(UserRepository):
    def __init__(self):
        self._users: Dict[str, User] = {}

    async def get_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        for user in self._users.values():
            if user.email.lower() == email.lower():
                return user
        return None

    async def save(self, user: User) -> User:
        self._users[user.id] = user
        return user
