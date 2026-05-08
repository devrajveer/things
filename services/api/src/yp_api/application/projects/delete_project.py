import ulid
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.audit.entities import AuditEvent
from yp_api.domain.auth.policy import PolicyEngine, ProjectPermission, ProjectContext
from yp_shared.errors import AppError

class ProjectNotFound(AppError):
    def __init__(self):
        super().__init__("Project not found", "not_found", 404)

class DeleteProjectUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, actor_id: str, project_id: str) -> None:
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
            
            PolicyEngine.assert_can(ProjectPermission.PROJECT_DELETE, context)
                
            await self.uow.projects.delete(project_id)
            
            audit = AuditEvent(
                id=f"aud_{ulid.new().str.lower()}",
                action="project.deleted",
                actor_id=actor_id,
                target_id=project_id,
                data={}
            )
            await self.uow.audit_events.save(audit)
            
            await self.uow.commit()
