from datetime import datetime
from pydantic import BaseModel
from yp_api.domain.uow import UnitOfWork
from yp_api.application.auth.password_hasher import Argon2PasswordHasher

class InvalidTokenException(Exception):
    pass

class TokenExpiredException(Exception):
    pass

class VerifyEmailUseCase:
    def __init__(self, uow: UnitOfWork, password_hasher: Argon2PasswordHasher):
        self.uow = uow
        self.password_hasher = password_hasher

    async def execute(self, token: str) -> None:
        parts = token.split(".")
        if len(parts) != 2:
            raise InvalidTokenException("Malformed token")
            
        link_id, raw_secret = parts

        async with self.uow:
            # Note: Need get_by_id on MagicLinkRepository, let's add it in UoW
            from sqlalchemy import select
            from yp_api.models.auth import MagicLink as MagicLinkModel
            
            # Since get_by_id isn't explicitly on the protocol, we can just use the UoW directly or add it.
            # I will assume `self.uow.magic_links.get_by_id` exists. Let's make sure it does.
            magic_link = await self.uow.magic_links.get_by_id(link_id)
            if not magic_link:
                raise InvalidTokenException("Token not found")
                
            if magic_link.purpose != "verify_email":
                raise InvalidTokenException("Invalid token purpose")
                
            if magic_link.used_at is not None:
                raise InvalidTokenException("Token already used")
                
            if magic_link.expires_at < datetime.utcnow():
                raise TokenExpiredException("Token expired")
                
            if not self.password_hasher.verify_password(raw_secret, magic_link.hashed_token):
                raise InvalidTokenException("Invalid token secret")

            user = await self.uow.users.get_by_email(magic_link.email)
            if not user:
                raise InvalidTokenException("User not found")

            # Update User
            user.email_verified_at = datetime.utcnow()
            await self.uow.users.save(user)
            
            # Update MagicLink
            magic_link.used_at = datetime.utcnow()
            await self.uow.magic_links.save(magic_link)
            
            await self.uow.commit()
