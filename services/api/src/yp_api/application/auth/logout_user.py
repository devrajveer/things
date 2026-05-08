from pydantic import BaseModel
from typing import Optional
from yp_api.domain.uow import UnitOfWork
from yp_shared.time import utc_now

class LogoutCommand(BaseModel):
    refresh_token: Optional[str] = None
    global_logout: bool = False

class LogoutUserUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, cmd: LogoutCommand) -> None:
        if not cmd.refresh_token or "." not in cmd.refresh_token:
            return

        try:
            token_id, _ = cmd.refresh_token.split(".", 1)
        except ValueError:
            return

        async with self.uow:
            token = await self.uow.refresh_tokens.get_by_id(token_id)
            if not token:
                return

            if cmd.global_logout:
                # Revoke all active sessions for this user
                await self.uow.refresh_tokens.revoke_all_for_user(token.user_id)
            else:
                # Revoke only the current session
                if token.used_at is None:
                    token.used_at = utc_now()
                    await self.uow.refresh_tokens.save(token)
            
            await self.uow.commit()
