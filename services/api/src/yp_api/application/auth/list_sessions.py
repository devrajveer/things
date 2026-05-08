from typing import List
from pydantic import BaseModel
from yp_api.domain.uow import UnitOfWork

class SessionDTO(BaseModel):
    id: str
    created_at: str
    expires_at: str

class ListUserSessionsUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: str) -> List[SessionDTO]:
        async with self.uow:
            tokens = await self.uow.refresh_tokens.get_active_by_user(user_id)
            
            return [
                SessionDTO(
                    id=t.id,
                    created_at=t.created_at.isoformat() if t.created_at else "",
                    expires_at=t.expires_at.isoformat()
                ) for t in tokens
            ]
