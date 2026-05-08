from typing import List
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.projects.entities import Project

class ListProjectsUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, actor_id: str) -> List[Project]:
        async with self.uow:
            # 1. Get all organizations user belongs to
            org_memberships = await self.uow.organizations.list_for_user(actor_id)
            
            project_ids = set()
            projects = []
            
            # 2. For each org, if they are admin/owner, they see all projects
            for org_member in org_memberships:
                if org_member.role in ["owner", "admin"]:
                    org_projects = await self.uow.projects.list_by_org(org_member.org_id)
                    for p in org_projects:
                        if p.id not in project_ids:
                            projects.append(p)
                            project_ids.add(p.id)
            
            # 3. Get all projects where they have explicit project-level membership
            member_projects = await self.uow.projects.list_by_user(actor_id)
            for p in member_projects:
                if p.id not in project_ids:
                    projects.append(p)
                    project_ids.add(p.id)
                
            return projects
