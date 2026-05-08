import ulid
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.audit.entities import AuditEvent
from yp_shared.errors import AppError

class RemoveMemberForbidden(AppError):
    def __init__(self, reason: str):
        super().__init__(reason, "forbidden", 403)

class RemoveMemberUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, org_id: str, actor_id: str, target_user_id: str) -> None:
        async with self.uow:
            actor = await self.uow.organizations.get_member(org_id, actor_id)
            if not actor or actor.role not in ["owner", "admin"]:
                raise RemoveMemberForbidden("Only owners and admins can remove members")
                
            target = await self.uow.organizations.get_member(org_id, target_user_id)
            if not target:
                raise RemoveMemberForbidden("Target user is not a member of this organization")
                
            if target.role == "owner":
                num_owners = await self.uow.organizations.count_owners(org_id)
                if num_owners <= 1:
                    raise RemoveMemberForbidden("Cannot remove the last owner of an organization")
                    
            await self.uow.organizations.delete_member(org_id, target_user_id)
            
            audit = AuditEvent(
                id=f"aud_{ulid.new().str.lower()}",
                action="member.removed",
                actor_id=actor_id,
                target_id=target_user_id,
                data={"org_id": org_id}
            )
            await self.uow.audit_events.save(audit)
            
            await self.uow.commit()
