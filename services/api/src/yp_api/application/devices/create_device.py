from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.devices.entities import Device, DeviceCredentials, DeviceStatus
from yp_api.domain.auth.policy import PolicyEngine, ProjectPermission, ProjectContext
from yp_api.application.devices.credential_service import CredentialService
from yp_api.application.organizations.quota_service import QuotaService
from yp_api.domain.organizations.quotas import QuotaKind
from yp_shared.errors import AppError
import uuid

@dataclass
class CreateDeviceCommand:
    project_id: str
    name: str
    profile_id: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None

class CreateDeviceUseCase:
    def __init__(self, uow: UnitOfWork, quota_service: QuotaService):
        self.uow = uow
        self.quota_service = quota_service

    async def execute(self, actor_id: str, cmd: CreateDeviceCommand) -> Tuple[Device, DeviceCredentials]:
        async with self.uow:
            # 1. Authorization & Existence
            project = await self.uow.projects.get(cmd.project_id)
            if not project:
                raise AppError("Project not found", status_code=404)

            org_member = await self.uow.organizations.get_member(project.org_id, actor_id)
            proj_member = await self.uow.project_members.get(cmd.project_id, actor_id)
            
            context = ProjectContext(
                org_role=org_member.role if org_member else None,
                project_role=proj_member.role if proj_member else None
            )
            PolicyEngine.assert_can(context, ProjectPermission.PROJECT_UPDATE)

            # 2. Quota Check
            await self.quota_service.check_quota(project.org_id, QuotaKind.DEVICES)

            # 3. Create Device
            device_id = f"dev_{uuid.uuid4().hex[:12]}"
            device = Device(
                id=device_id,
                project_id=cmd.project_id,
                profile_id=cmd.profile_id,
                name=cmd.name,
                labels=cmd.labels,
                description=cmd.description,
                status=DeviceStatus.PROVISIONED
            )

            # 4. Generate Credentials
            mqtt_user, mqtt_pass, http_token, mqtt_hash, http_hash = CredentialService.generate_device_credentials(device_id)
            
            creds = DeviceCredentials(
                device_id=device_id,
                mqtt_username=mqtt_user,
                mqtt_password=mqtt_pass,  # Plain for return
                mqtt_password_hash=mqtt_hash,
                http_token=http_token,    # Plain for return
                http_token_hash=http_hash
            )

            # 5. Save
            await self.uow.devices.save(device)
            await self.uow.devices.save_credentials(creds)
            
            await self.uow.commit()
            
            return device, creds
            
