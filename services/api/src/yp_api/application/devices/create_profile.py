from dataclasses import dataclass
from typing import Dict, Any, Optional
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.devices.entities import DeviceProfile, PayloadFormat
from yp_api.domain.auth.policy import PolicyEngine, ProjectPermission, ProjectContext
from yp_shared.errors import AppError
import uuid

class DeviceProfileNameExists(AppError):
    code = "already_exists"
    status_code = 409

@dataclass
class CreateDeviceProfileCommand:
    project_id: str
    name: str
    schema: Dict[str, Any]
    payload_format: str = "json"
    decoder_js: Optional[str] = None

class CreateDeviceProfileUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, actor_id: str, cmd: CreateDeviceProfileCommand) -> DeviceProfile:
        async with self.uow:
            # 1. Authorization
            project = await self.uow.projects.get(cmd.project_id)
            if not project:
                raise AppError("Project not found", status_code=404)

            # Get member role for policy engine
            org_member = await self.uow.organizations.get_member(project.org_id, actor_id)
            proj_member = await self.uow.project_members.get(cmd.project_id, actor_id)
            
            context = ProjectContext(
                org_role=org_member.role if org_member else None,
                project_role=proj_member.role if proj_member else None
            )
            PolicyEngine.assert_can(context, ProjectPermission.PROJECT_UPDATE) # Or DEVICE_PROFILE_CREATE if we had it

            # 2. Check name uniqueness in project
            profiles = await self.uow.device_profiles.list_by_project(cmd.project_id)
            if any(p.name == cmd.name for p in profiles):
                raise DeviceProfileNameExists(f"Device profile with name '{cmd.name}' already exists in this project")

            # 3. Create entity
            profile = DeviceProfile(
                id=f"dpf_{uuid.uuid4().hex[:12]}",
                project_id=cmd.project_id,
                name=cmd.name,
                schema=cmd.schema,
                payload_format=PayloadFormat(cmd.payload_format),
                decoder_js=cmd.decoder_js
            )

            await self.uow.device_profiles.save(profile)
            await self.uow.commit()
            return profile
