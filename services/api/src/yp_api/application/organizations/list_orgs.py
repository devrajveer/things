from typing import List
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.organizations.entities import Organization

class ListOrganizationsUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: str) -> List[Organization]:
        async with self.uow:
            return await self.uow.organizations.list_for_user(user_id)
