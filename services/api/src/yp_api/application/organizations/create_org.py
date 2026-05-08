import ulid
from pydantic import BaseModel
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.organizations.entities import Organization, OrganizationMember

class CreateOrganizationCommand(BaseModel):
    name: str

class CreateOrganizationUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: str, cmd: CreateOrganizationCommand) -> Organization:
        org_id = f"org_{ulid.new().str.lower()}"
        
        org = Organization(
            id=org_id,
            name=cmd.name,
            owner_id=user_id,
            tier="free"
        )
        
        member = OrganizationMember(
            org_id=org_id,
            user_id=user_id,
            role="owner"
        )
        
        async with self.uow:
            await self.uow.organizations.save(org)
            await self.uow.organizations.save_member(member)
            await self.uow.commit()
            
        return org
