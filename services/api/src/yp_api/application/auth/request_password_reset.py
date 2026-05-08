import ulid
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.users.entities import MagicLink
from yp_api.domain.services.email import EmailService
from yp_api.application.auth.password_hasher import Argon2PasswordHasher
from yp_shared.time import utc_now

class RequestPasswordResetCommand(BaseModel):
    email: EmailStr

class RequestPasswordResetUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: Argon2PasswordHasher,
        email_service: EmailService
    ):
        self.uow = uow
        self.password_hasher = password_hasher
        self.email_service = email_service

    async def execute(self, cmd: RequestPasswordResetCommand) -> None:
        async with self.uow:
            user = await self.uow.users.get_by_email(cmd.email)
            if not user:
                # Return success to prevent enumeration
                return

            # Generate Magic Link
            magic_link_id = f"mgl_{ulid.new().str.lower()}"
            raw_secret = ulid.new().str
            token = f"{magic_link_id}.{raw_secret}"
            
            hashed_token = self.password_hasher.hash_password(raw_secret)
            
            magic_link = MagicLink(
                id=magic_link_id,
                email=user.email,
                hashed_token=hashed_token,
                purpose="password_reset",
                expires_at=utc_now() + timedelta(hours=1)
            )
            await self.uow.magic_links.save(magic_link)
            await self.uow.commit()

        # Send Email
        await self.email_service.send_password_reset_email(user.email, user.name, token)
