import ulid
import secrets
from passlib.hash import argon2
from datetime import datetime, timedelta
from pydantic import BaseModel
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.organizations.entities import OrganizationInvite
from yp_api.domain.audit.entities import AuditEvent
from yp_shared.errors import AppError
import logging

logger = logging.getLogger(__name__)

class InviteMemberForbidden(AppError):
    def __init__(self, reason: str):
        super().__init__(reason, "forbidden", 403)

class InviteMemberCommand(BaseModel):
    email: str
    role: str

class InviteMemberUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, org_id: str, actor_id: str, cmd: InviteMemberCommand) -> dict:
        async with self.uow:
            member = await self.uow.organizations.get_member(org_id, actor_id)
            if not member or member.role not in ["owner", "admin"]:
                raise InviteMemberForbidden("Only owners and admins can invite members")
            
            invite_id = f"inv_{ulid.new().str.lower()}"
            raw_secret = secrets.token_urlsafe(32)
            hashed_secret = argon2.hash(raw_secret)
            token_to_send = f"{invite_id}.{raw_secret}"
            
            invite = OrganizationInvite(
                id=invite_id,
                org_id=org_id,
                email=cmd.email.lower(),
                role=cmd.role,
                hashed_token=hashed_secret,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            
            await self.uow.organization_invites.save(invite)
            
            audit = AuditEvent(
                id=f"aud_{ulid.new().str.lower()}",
                action="member.invited",
                actor_id=actor_id,
                target_id=invite.id,
                data={"email": cmd.email, "role": cmd.role}
            )
            await self.uow.audit_events.save(audit)
            
            await self.uow.commit()
            
            logger.info(f"MOCK EMAIL: To={cmd.email}, Link=https://app.megaiot/invites/accept?token={token_to_send}")
            
            return {"invite_id": invite.id}
