from typing import List
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.organizations.entities import OrganizationInvite
from yp_shared.errors import AppError

class ListInvitesForbidden(AppError):
    def __init__(self):
        super().__init__("Only admins and owners can view invites", "forbidden", 403)

class ListInvitesUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, org_id: str, actor_id: str) -> List[OrganizationInvite]:
        async with self.uow:
            actor = await self.uow.organizations.get_member(org_id, actor_id)
            if not actor or actor.role not in ["owner", "admin"]:
                raise ListInvitesForbidden()
                
            return await self.uow.organization_invites.list_by_org(org_id)
