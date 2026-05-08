from pydantic import BaseModel
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.organizations.entities import Organization
from yp_shared.errors import AppError

class OrganizationNotFound(AppError):
    def __init__(self, org_id: str):
        super().__init__(f"Organization {org_id} not found", "not_found", 404)

class OrganizationUpdateForbidden(AppError):
    def __init__(self, reason: str):
        super().__init__(reason, "forbidden", 403)

class UpdateOrganizationCommand(BaseModel):
    name: str

class UpdateOrganizationUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, org_id: str, user_id: str, cmd: UpdateOrganizationCommand) -> Organization:
        async with self.uow:
            org = await self.uow.organizations.get_by_id(org_id)
            if not org:
                raise OrganizationNotFound(org_id)
                
            member = await self.uow.organizations.get_member(org_id, user_id)
            if not member or member.role != "owner":
                raise OrganizationUpdateForbidden("Only owners can update an organization")
                
            if org.name == "Personal" and cmd.name != "Personal":
                raise OrganizationUpdateForbidden("Cannot change the name of the Personal organization")
                
            org.name = cmd.name
            await self.uow.organizations.save(org)
            await self.uow.commit()
            
            return org
