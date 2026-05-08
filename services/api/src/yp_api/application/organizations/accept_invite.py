import ulid
from passlib.hash import argon2
from datetime import datetime
from pydantic import BaseModel
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.organizations.entities import OrganizationMember
from yp_api.domain.audit.entities import AuditEvent
from yp_shared.errors import AppError

class InvalidInvite(AppError):
    def __init__(self):
        super().__init__("Invalid or expired invite token", "invalid_invite", 400)

class AcceptInviteCommand(BaseModel):
    token: str

class AcceptInviteUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: str, user_email: str, cmd: AcceptInviteCommand) -> str:
        try:
            invite_id, secret = cmd.token.split(".", 1)
        except ValueError:
            raise InvalidInvite()
            
        async with self.uow:
            invite = await self.uow.organization_invites.get_by_id(invite_id)
            if not invite or invite.accepted_at or invite.expires_at < datetime.utcnow():
                raise InvalidInvite()
                
            if invite.email.lower() != user_email.lower():
                raise InvalidInvite()
                
            if not argon2.verify(secret, invite.hashed_token):
                raise InvalidInvite()
                
            member = OrganizationMember(
                org_id=invite.org_id,
                user_id=user_id,
                role=invite.role
            )
            await self.uow.organizations.save_member(member)
            
            invite.accepted_at = datetime.utcnow()
            await self.uow.organization_invites.save(invite)
            
            audit = AuditEvent(
                id=f"aud_{ulid.new().str.lower()}",
                action="member.accepted",
                actor_id=user_id,
                target_id=invite.org_id,
                data={"invite_id": invite.id}
            )
            await self.uow.audit_events.save(audit)
            
            await self.uow.commit()
            return invite.org_id
