import ulid
from datetime import timedelta
from pydantic import BaseModel
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.users.entities import RefreshToken
from yp_api.application.auth.password_hasher import Argon2PasswordHasher
from yp_api.application.auth.token_service import TokenService
from yp_shared.errors import AppError
from yp_shared.time import utc_now

class InvalidTokenException(AppError):
    def __init__(self, message: str = "Invalid or expired refresh token"):
        super().__init__(message, code="invalid_token")

class TokenReuseException(AppError):
    def __init__(self, message: str = "Security alert: token reuse detected"):
        super().__init__(message, code="token_reuse")

class RotateTokensCommand(BaseModel):
    refresh_token: str

class RotateTokensUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: Argon2PasswordHasher,
        token_service: TokenService
    ):
        self.uow = uow
        self.password_hasher = password_hasher
        self.token_service = token_service

    async def execute(self, cmd: RotateTokensCommand) -> dict:
        # 1. Parse token (expected format: id.secret)
        if "." not in cmd.refresh_token:
            raise InvalidTokenException()
            
        try:
            token_id, raw_secret = cmd.refresh_token.split(".", 1)
        except ValueError:
            raise InvalidTokenException()

        async with self.uow:
            # 2. Lookup token
            token = await self.uow.refresh_tokens.get_by_id(token_id)
            if not token:
                raise InvalidTokenException()

            # 3. Verification
            if not self.password_hasher.verify_password(raw_secret, token.hashed_token):
                raise InvalidTokenException()

            if token.expires_at < utc_now():
                raise InvalidTokenException("Refresh token has expired")

            # 4. Reuse Detection (§4.4)
            if token.used_at is not None:
                # REUSE DETECTED!
                await self.uow.refresh_tokens.revoke_all_for_user(token.user_id)
                await self.uow.commit()
                raise TokenReuseException()

            # 5. Success - Mark current as used and generate new ones
            token.used_at = utc_now()
            await self.uow.refresh_tokens.save(token)

            access_token = self.token_service.create_access_token(token.user_id)
            
            new_token_id = f"rtk_{ulid.new().str.lower()}"
            new_raw_secret = self.token_service.create_refresh_token_string()
            new_refresh_token_string = f"{new_token_id}.{new_raw_secret}"
            
            new_hashed_rt = self.password_hasher.hash_password(new_raw_secret)
            new_refresh_token = RefreshToken(
                id=new_token_id,
                user_id=token.user_id,
                hashed_token=new_hashed_rt,
                expires_at=utc_now() + timedelta(days=30)
            )
            await self.uow.refresh_tokens.save(new_refresh_token)
            
            user = await self.uow.users.get_by_id(token.user_id)
            await self.uow.commit()

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": new_refresh_token_string,
            "expires_in": 900
        }
