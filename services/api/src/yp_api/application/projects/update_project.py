import ulid
from pydantic import BaseModel
from typing import Optional
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.projects.entities import Project
from yp_api.domain.audit.entities import AuditEvent
from yp_api.domain.auth.policy import PolicyEngine, ProjectPermission, ProjectContext
from yp_shared.errors import AppError

class ProjectNotFound(AppError):
    def __init__(self):
        super().__init__("Project not found", "not_found", 404)

class UpdateProjectCommand(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class UpdateProjectUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, actor_id: str, project_id: str, cmd: UpdateProjectCommand) -> Project:
        async with self.uow:
            project = await self.uow.projects.get(project_id)
            if not project:
                raise ProjectNotFound()
                
            org_member = await self.uow.organizations.get_member(project.org_id, actor_id)
            project_member = await self.uow.project_members.get(project_id, actor_id)
            
            context = ProjectContext(
                org_role=org_member.role if org_member else None,
                project_role=project_member.role if project_member else None
            )
            
            PolicyEngine.assert_can(ProjectPermission.PROJECT_UPDATE, context)
                
            if cmd.name is not None:
                project.name = cmd.name
            if cmd.description is not None:
                project.description = cmd.description
                
            await self.uow.projects.save(project)
            
            audit = AuditEvent(
                id=f"aud_{ulid.new().str.lower()}",
                action="project.updated",
                actor_id=actor_id,
                target_id=project_id,
                data=cmd.model_dump(exclude_unset=True)
            )
            await self.uow.audit_events.save(audit)
            
            await self.uow.commit()
            return project
