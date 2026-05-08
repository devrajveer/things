import ulid
from datetime import timedelta
from pydantic import BaseModel
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.users.entities import RefreshToken
from yp_api.application.auth.password_hasher import Argon2PasswordHasher
from yp_api.application.auth.token_service import TokenService
from yp_shared.time import utc_now
from yp_shared.errors import AppError

class InvalidMagicLinkException(AppError):
    def __init__(self, message: str = "Invalid or expired login link"):
        super().__init__(message, code="invalid_magic_link")

class VerifyMagicLinkCommand(BaseModel):
    token: str

class VerifyMagicLinkUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: Argon2PasswordHasher,
        token_service: TokenService
    ):
        self.uow = uow
        self.password_hasher = password_hasher
        self.token_service = token_service

    async def execute(self, cmd: VerifyMagicLinkCommand) -> dict:
        if "." not in cmd.token:
            raise InvalidMagicLinkException()
            
        try:
            link_id, raw_secret = cmd.token.split(".", 1)
        except ValueError:
            raise InvalidMagicLinkException()

        async with self.uow:
            link = await self.uow.magic_links.get_by_id(link_id)
            if not link or link.purpose != "login":
                raise InvalidMagicLinkException()

            if not self.password_hasher.verify_password(raw_secret, link.hashed_token):
                raise InvalidMagicLinkException()

            if link.expires_at < utc_now():
                raise InvalidMagicLinkException("Login link has expired")

            if link.used_at is not None:
                raise InvalidMagicLinkException("Login link has already been used")

            # Link is valid, fetch user
            user = await self.uow.users.get_by_email(link.email)
            if not user or user.status != "active":
                raise InvalidMagicLinkException()

            # Create session
            access_token = self.token_service.create_access_token(user.id)
            
            rt_id = f"rtk_{ulid.new().str.lower()}"
            rt_raw = self.token_service.create_refresh_token_string()
            rt_string = f"{rt_id}.{rt_raw}"
            
            rt_hashed = self.password_hasher.hash_password(rt_raw)
            refresh_token = RefreshToken(
                id=rt_id,
                user_id=user.id,
                hashed_token=rt_hashed,
                expires_at=utc_now() + timedelta(days=30)
            )
            await self.uow.refresh_tokens.save(refresh_token)
            
            # Mark link as used
            link.used_at = utc_now()
            await self.uow.magic_links.save(link)
            
            await self.uow.commit()

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": rt_string,
            "expires_in": 900
        }
