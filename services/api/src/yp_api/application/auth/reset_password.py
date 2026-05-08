from pydantic import BaseModel
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.users.password_policy import validate_password
from yp_api.application.auth.password_hasher import Argon2PasswordHasher
from yp_api.domain.services.email import EmailService
from yp_shared.time import utc_now
from yp_shared.errors import AppError

class InvalidResetTokenException(AppError):
    def __init__(self, message: str = "Invalid or expired reset token"):
        super().__init__(message, code="invalid_reset_token")

class ResetPasswordCommand(BaseModel):
    token: str
    new_password: str

class ResetPasswordUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: Argon2PasswordHasher,
        email_service: EmailService
    ):
        self.uow = uow
        self.password_hasher = password_hasher
        self.email_service = email_service

    async def execute(self, cmd: ResetPasswordCommand) -> None:
        # 1. Parse token
        if "." not in cmd.token:
            raise InvalidResetTokenException()
            
        try:
            link_id, raw_secret = cmd.token.split(".", 1)
        except ValueError:
            raise InvalidResetTokenException()

        # 2. Validate Password Policy
        validate_password(cmd.new_password)

        async with self.uow:
            # 3. Lookup Magic Link
            link = await self.uow.magic_links.get_by_id(link_id)
            if not link or link.purpose != "password_reset":
                raise InvalidResetTokenException()

            # 4. Verification
            if not self.password_hasher.verify_password(raw_secret, link.hashed_token):
                raise InvalidResetTokenException()

            if link.expires_at < utc_now():
                raise InvalidResetTokenException("Reset token has expired")

            if link.used_at is not None:
                raise InvalidResetTokenException("Reset token has already been used")

            # 5. Fetch User
            user = await self.uow.users.get_by_email(link.email)
            if not user:
                raise InvalidResetTokenException()

            # 6. Update Password and Revoke Sessions
            new_hash = self.password_hasher.hash_password(cmd.new_password)
            user.password_hash = new_hash
            await self.uow.users.save(user)
            
            # Global session revocation (§2.4)
            await self.uow.refresh_tokens.revoke_all_for_user(user.id)
            
            # 7. Finalize Link
            link.used_at = utc_now()
            await self.uow.magic_links.save(link)
            
            await self.uow.commit()

        # 8. Send Confirmation Email
        await self.email_service.send_password_changed_notification(user.email, user.name)
