from typing import List
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.organizations.entities import OrganizationMember
from yp_shared.errors import AppError

class ListMembersForbidden(AppError):
    def __init__(self):
        super().__init__("Only members can view the member list", "forbidden", 403)

class ListMembersUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, org_id: str, actor_id: str) -> List[OrganizationMember]:
        async with self.uow:
            actor = await self.uow.organizations.get_member(org_id, actor_id)
            if not actor:
                raise ListMembersForbidden()
                
            return await self.uow.organizations.list_members(org_id)
