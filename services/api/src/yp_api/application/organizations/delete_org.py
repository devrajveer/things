from yp_api.domain.uow import UnitOfWork
from yp_shared.errors import AppError

class OrganizationNotFound(AppError):
    def __init__(self, org_id: str):
        super().__init__(f"Organization {org_id} not found", "not_found", 404)

class OrganizationDeleteForbidden(AppError):
    def __init__(self, reason: str):
        super().__init__(reason, "forbidden", 403)

class DeleteOrganizationUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, org_id: str, user_id: str) -> None:
        async with self.uow:
            org = await self.uow.organizations.get_by_id(org_id)
            if not org:
                raise OrganizationNotFound(org_id)
                
            member = await self.uow.organizations.get_member(org_id, user_id)
            if not member or member.role != "owner":
                raise OrganizationDeleteForbidden("Only owners can delete an organization")
                
            if org.name == "Personal":
                raise OrganizationDeleteForbidden("Cannot delete the Personal organization")
                
            await self.uow.organizations.delete(org_id)
            await self.uow.commit()
