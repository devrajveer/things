from typing import Protocol, Optional
from yp_api.domain.users.entities import User

class UserRepository(Protocol):
    async def get_by_id(self, user_id: str) -> Optional[User]:
        ...

    async def get_by_email(self, email: str) -> Optional[User]:
        ...

    async def save(self, user: User) -> User:
        ...
