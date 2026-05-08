import ulid
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.users.entities import RefreshToken
from yp_api.application.auth.password_hasher import Argon2PasswordHasher
from yp_api.application.auth.token_service import TokenService
from yp_api.application.auth.rate_limiter import LoginRateLimiter
from yp_shared.errors import AppError
from yp_shared.time import utc_now

class InvalidCredentialsException(AppError):
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message, code="invalid_credentials")

class LoginCommand(BaseModel):
    email: EmailStr
    password: str
    ip_address: str

class LoginUserUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: Argon2PasswordHasher,
        token_service: TokenService,
        rate_limiter: LoginRateLimiter
    ):
        self.uow = uow
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.rate_limiter = rate_limiter

    async def execute(self, cmd: LoginCommand) -> dict:
        await self.rate_limiter.check_rate_limit(cmd.email, cmd.ip_address)

        async with self.uow:
            user = await self.uow.users.get_by_email(cmd.email)
            
            if not user:
                # Help prevent timing attacks
                # Note: Argon2 verify on a dummy string is still relatively fast, 
                # but better than an immediate return.
                self.password_hasher.verify_password(cmd.password, "$argon2id$v=19$m=65536,t=3,p=4$dummyhashdummyhash")
                await self.rate_limiter.record_failure(cmd.email, cmd.ip_address)
                raise InvalidCredentialsException()

            if not self.password_hasher.verify_password(cmd.password, user.password_hash):
                await self.rate_limiter.record_failure(cmd.email, cmd.ip_address)
                raise InvalidCredentialsException()

            # Success
            await self.rate_limiter.reset(cmd.email, cmd.ip_address)

            access_token = self.token_service.create_access_token(user.id)
            
            # Use id.secret format for efficient lookup during rotation
            token_id = f"rtk_{ulid.new().str.lower()}"
            raw_secret = self.token_service.create_refresh_token_string()
            refresh_token_string = f"{token_id}.{raw_secret}"
            
            # Save hashed refresh token
            hashed_rt = self.password_hasher.hash_password(raw_secret)
            refresh_token = RefreshToken(
                id=token_id,
                user_id=user.id,
                hashed_token=hashed_rt,
                expires_at=utc_now() + timedelta(days=30)
            )
            await self.uow.refresh_tokens.save(refresh_token)
            await self.uow.commit()

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token_string,
            "expires_in": 900
        }
