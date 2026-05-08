from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from yp_api.domain.users.entities import User as UserEntity
from yp_api.domain.users.repository import UserRepository
from yp_api.models.auth import User as UserModel

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> Optional[UserEntity]:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        if model:
            return UserEntity.model_validate(model)
        return None

    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        # CITEXT will handle case-insensitivity in Postgres
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        if model:
            return UserEntity.model_validate(model)
        return None

    async def save(self, user: UserEntity) -> UserEntity:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user.id))
        model = result.scalar_one_or_none()
        
        if not model:
            model = UserModel(**user.model_dump())
            self.session.add(model)
        else:
            for key, value in user.model_dump().items():
                setattr(model, key, value)
                
        await self.session.flush()
        return UserEntity.model_validate(model)
