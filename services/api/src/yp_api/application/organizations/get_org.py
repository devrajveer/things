from yp_api.domain.uow import UnitOfWork
from yp_api.domain.organizations.entities import Organization
from yp_shared.errors import AppError

class OrganizationNotFound(AppError):
    def __init__(self, org_id: str):
        super().__init__(f"Organization {org_id} not found", "not_found", 404)

class OrganizationAccessDenied(AppError):
    def __init__(self):
        super().__init__("Access denied to organization", "forbidden", 403)

class GetOrganizationUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, org_id: str, user_id: str) -> Organization:
        async with self.uow:
            org = await self.uow.organizations.get_by_id(org_id)
            if not org:
                raise OrganizationNotFound(org_id)
            
            member = await self.uow.organizations.get_member(org_id, user_id)
            if not member:
                raise OrganizationAccessDenied()
            
            return org
