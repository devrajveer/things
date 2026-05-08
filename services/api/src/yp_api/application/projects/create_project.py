import ulid
import re
from pydantic import BaseModel
from typing import Optional
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.projects.entities import Project
from yp_api.domain.audit.entities import AuditEvent
from yp_api.domain.auth.policy import PolicyEngine, ProjectPermission, ProjectContext
from yp_api.application.organizations.quota_service import QuotaService
from yp_api.domain.devices.entities import DeviceProfile, PayloadFormat
from yp_shared.errors import AppError

class InvalidProjectSlug(AppError):
    def __init__(self, reason: str):
        super().__init__(reason, "validation_failed", 422)

class ProjectSlugExists(AppError):
    def __init__(self):
        super().__init__("Project with this name/slug already exists in the organization", "already_exists", 409)

class CreateProjectCommand(BaseModel):
    name: str
    organization_id: str
    description: Optional[str] = None

RESERVED_SLUGS = {
    "time", "timestamp", "device_id", "project_id", "id", "_meta", "_ingested_at", "_source", "_quality",
    "api", "admin", "settings", "new"
}

class CreateProjectUseCase:
    def __init__(self, uow: UnitOfWork, quota_service: Optional[QuotaService] = None):
        self.uow = uow
        self.quota_service = quota_service

    async def execute(self, actor_id: str, cmd: CreateProjectCommand) -> Project:
        async with self.uow:
            from yp_api.domain.organizations.quotas import QuotaKind
            if self.quota_service:
                await self.quota_service.check_quota(cmd.organization_id, QuotaKind.PROJECTS)

            org_member = await self.uow.organizations.get_member(cmd.organization_id, actor_id)
            
            context = ProjectContext(
                org_role=org_member.role if org_member else None,
                project_role=None # No project role yet
            )
            
            PolicyEngine.assert_can(ProjectPermission.PROJECT_CREATE, context)
            
            slug = re.sub(r'[^a-z0-9]+', '-', cmd.name.lower()).strip('-')
            if not slug or slug in RESERVED_SLUGS:
                raise InvalidProjectSlug(f"Invalid or reserved project name: {cmd.name}")
                
            exists = await self.uow.projects.check_slug_exists(cmd.organization_id, slug)
            if exists:
                raise ProjectSlugExists()
                
            project_id = f"prj_{ulid.new().str.lower()}"
            
            project = Project(
                id=project_id,
                org_id=cmd.organization_id,
                name=cmd.name,
                slug=slug,
                description=cmd.description
            )
            
            await self.uow.projects.save(project)
            
            # Auto-assign the creator as the project owner
            from yp_api.domain.projects.entities import ProjectMember
            member = ProjectMember(
                project_id=project_id,
                user_id=actor_id,
                role="owner"
            )
            await self.uow.project_members.save(member)

            # Seed default profiles
            import uuid
            default_profiles = [
                DeviceProfile(
                    id=f"dpf_{uuid.uuid4().hex[:12]}",
                    project_id=project_id,
                    name="Generic HTTP",
                    payload_format=PayloadFormat.JSON,
                    schema={}
                ),
                DeviceProfile(
                    id=f"dpf_{uuid.uuid4().hex[:12]}",
                    project_id=project_id,
                    name="Generic MQTT",
                    payload_format=PayloadFormat.JSON,
                    schema={}
                )
            ]
            for p in default_profiles:
                await self.uow.device_profiles.save(p)
            
            audit = AuditEvent(
                id=f"aud_{ulid.new().str.lower()}",
                action="project.created",
                actor_id=actor_id,
                target_id=project_id,
                data={"name": cmd.name, "org_id": cmd.organization_id}
            )
            await self.uow.audit_events.save(audit)
            
            await self.uow.commit()
            return project
