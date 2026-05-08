from pydantic import BaseModel
from yp_api.domain.uow import UnitOfWork
from yp_shared.time import utc_now

class RevokeSessionCommand(BaseModel):
    session_id: str
    user_id: str

class RevokeSessionUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, cmd: RevokeSessionCommand) -> None:
        async with self.uow:
            token = await self.uow.refresh_tokens.get_by_id_and_user(cmd.session_id, cmd.user_id)
            if token and token.used_at is None:
                token.used_at = utc_now()
                await self.uow.refresh_tokens.save(token)
                await self.uow.commit()
