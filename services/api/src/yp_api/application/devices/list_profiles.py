from typing import List
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.devices.entities import DeviceProfile
from yp_api.domain.auth.policy import PolicyEngine, ProjectPermission, ProjectContext
from yp_shared.errors import AppError

class ListDeviceProfilesUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, actor_id: str, project_id: str) -> List[DeviceProfile]:
        async with self.uow:
            # 1. Authorization
            project = await self.uow.projects.get(project_id)
            if not project:
                raise AppError("Project not found", status_code=404)

            org_member = await self.uow.organizations.get_member(project.org_id, actor_id)
            proj_member = await self.uow.project_members.get(project_id, actor_id)
            
            context = ProjectContext(
                org_role=org_member.role if org_member else None,
                project_role=proj_member.role if proj_member else None
            )
            PolicyEngine.assert_can(context, ProjectPermission.PROJECT_VIEW)

            # 2. List
            return await self.uow.device_profiles.list_by_project(project_id)
