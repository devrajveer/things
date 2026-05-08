from datetime import datetime, timedelta
import ulid
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.users.entities import MagicLink
from yp_api.application.auth.password_hasher import Argon2PasswordHasher
from yp_api.domain.services.email import EmailService

class RateLimitExceededException(Exception):
    pass

class UserNotFoundException(Exception):
    pass

class ResendVerificationEmailUseCase:
    def __init__(self, uow: UnitOfWork, password_hasher: Argon2PasswordHasher, email_service: EmailService):
        self.uow = uow
        self.password_hasher = password_hasher
        self.email_service = email_service

    async def execute(self, email: str) -> None:
        async with self.uow:
            user = await self.uow.users.get_by_email(email)
            if not user:
                # Return silently to prevent email enumeration, or raise. 
                # Specs say we usually return sent: true. Let's raise and handle in router, or just return.
                return

            if user.email_verified_at is not None:
                # Already verified, ignore.
                return

            # Check rate limit (1 per 60s)
            latest_link = await self.uow.magic_links.get_latest_for_email(email, "verify_email")
            if latest_link:
                time_since_creation = (datetime.utcnow() - latest_link.created_at.replace(tzinfo=None)).total_seconds()
                if time_since_creation < 60:
                    raise RateLimitExceededException("Please wait 60 seconds before requesting a new email")

            magic_link_id = f"mgl_{ulid.new().str.lower()}"
            raw_secret = ulid.new().str
            verification_token = f"{magic_link_id}.{raw_secret}"
            hashed_vt = self.password_hasher.hash_password(raw_secret)

            magic_link = MagicLink(
                id=magic_link_id,
                email=user.email,
                hashed_token=hashed_vt,
                purpose="verify_email",
                expires_at=datetime.utcnow() + timedelta(days=1)
            )
            await self.uow.magic_links.save(magic_link)
            await self.uow.commit()

        # Send email outside of UoW
        await self.email_service.send_verification_email(user.email, user.name, verification_token)
