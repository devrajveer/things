import ulid
from pydantic import BaseModel
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.audit.entities import AuditEvent
from yp_shared.errors import AppError

class UpdateMemberForbidden(AppError):
    def __init__(self, reason: str):
        super().__init__(reason, "forbidden", 403)

class UpdateMemberCommand(BaseModel):
    role: str

class UpdateMemberUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, org_id: str, actor_id: str, target_user_id: str, cmd: UpdateMemberCommand) -> None:
        async with self.uow:
            actor = await self.uow.organizations.get_member(org_id, actor_id)
            if not actor or actor.role not in ["owner", "admin"]:
                raise UpdateMemberForbidden("Only owners and admins can update members")
                
            target = await self.uow.organizations.get_member(org_id, target_user_id)
            if not target:
                raise UpdateMemberForbidden("Target user is not a member of this organization")
                
            if target.role == "owner" and cmd.role != "owner":
                num_owners = await self.uow.organizations.count_owners(org_id)
                if num_owners <= 1:
                    raise UpdateMemberForbidden("Cannot demote the last owner of an organization")
                    
            target.role = cmd.role
            await self.uow.organizations.save_member(target)
            
            audit = AuditEvent(
                id=f"aud_{ulid.new().str.lower()}",
                action="member.role_changed",
                actor_id=actor_id,
                target_id=target_user_id,
                data={"org_id": org_id, "new_role": cmd.role}
            )
            await self.uow.audit_events.save(audit)
            
            await self.uow.commit()
