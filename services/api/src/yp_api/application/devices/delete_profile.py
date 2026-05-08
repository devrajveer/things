from yp_api.domain.uow import UnitOfWork
from yp_api.domain.auth.policy import PolicyEngine, ProjectPermission, ProjectContext
from yp_shared.errors import AppError

class DeviceProfileInUse(AppError):
    code = "resource_in_use"
    status_code = 409

class DeleteDeviceProfileUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, actor_id: str, project_id: str, profile_id: str) -> None:
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
            PolicyEngine.assert_can(context, ProjectPermission.PROJECT_UPDATE)

            # 2. Check existence
            profile = await self.uow.device_profiles.get(profile_id)
            if not profile or profile.project_id != project_id:
                raise AppError("Device profile not found", status_code=404)

            # 3. Check usage
            device_count = await self.uow.devices.count_by_profile(profile_id)
            if device_count > 0:
                raise DeviceProfileInUse(f"Cannot delete profile '{profile.name}' because {device_count} devices are using it")

            # 4. Delete
            await self.uow.device_profiles.delete(profile_id)
            await self.uow.commit()
