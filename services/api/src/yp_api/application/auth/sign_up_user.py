import ulid
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.users.entities import User, MagicLink
from yp_api.domain.organizations.entities import Organization, OrganizationMember
from yp_api.domain.projects.entities import Project
from yp_api.domain.users.password_policy import validate_password
from yp_api.application.auth.password_hasher import Argon2PasswordHasher
from yp_api.application.auth.token_service import TokenService
from yp_api.domain.services.email import EmailService

class EmailTakenException(Exception):
    pass

class SignUpCommand(BaseModel):
    email: EmailStr
    password: str
    name: str

class SignUpUserUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: Argon2PasswordHasher,
        token_service: TokenService,
        email_service: EmailService
    ):
        self.uow = uow
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.email_service = email_service

    async def execute(self, cmd: SignUpCommand) -> dict:
        validate_password(cmd.password)

        async with self.uow:
            existing = await self.uow.users.get_by_email(cmd.email)
            if existing:
                raise EmailTakenException(cmd.email)

            user_id = f"usr_{ulid.new().str.lower()}"
            org_id = f"org_{ulid.new().str.lower()}"
            project_id = f"prj_{ulid.new().str.lower()}"

            hashed_password = self.password_hasher.hash_password(cmd.password)

            user = User(
                id=user_id,
                email=cmd.email,
                password_hash=hashed_password,
                name=cmd.name,
                status="active"
            )

            org = Organization(
                id=org_id,
                name="Personal",
                owner_id=user_id,
                tier="free"
            )

            membership = OrganizationMember(
                org_id=org_id,
                user_id=user_id,
                role="owner"
            )

            project = Project(
                id=project_id,
                org_id=org_id,
                name="My Project",
                slug=f"my-project-{ulid.new().str[-6:].lower()}"
            )

            access_token = self.token_service.create_access_token(user_id)
            refresh_token_string = self.token_service.create_refresh_token_string()
            
            await self.uow.users.save(user)
            await self.uow.organizations.save(org)
            await self.uow.organizations.save_member(membership)
            await self.uow.projects.save(project)
            
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

        await self.email_service.send_verification_email(user.email, user.name, verification_token)

        return {
            "user": user,
            "organization": org,
            "project": project,
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token_string,
                "expires_in": 900,
                "token_type": "Bearer"
            }
        }
