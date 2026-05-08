from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from yp_api.domain.users.entities import User
from yp_api.interfaces.http.dependencies import (
    get_current_user,
    get_create_project_use_case,
    get_get_project_use_case,
    get_list_projects_use_case,
    get_update_project_use_case,
    get_delete_project_use_case,
    require_project_permission
)
from yp_api.domain.auth.policy import ProjectPermission
from yp_api.application.projects.create_project import CreateProjectUseCase, CreateProjectCommand, InvalidProjectSlug, ProjectSlugExists
from yp_api.application.organizations.quota_service import QuotaExceededError
from yp_api.application.projects.get_project import GetProjectUseCase, ProjectNotFound
from yp_api.application.projects.list_projects import ListProjectsUseCase
from yp_api.application.projects.update_project import UpdateProjectUseCase, UpdateProjectCommand
from yp_api.application.projects.delete_project import DeleteProjectUseCase
from yp_api.interfaces.http.v1.device_profiles import router as device_profiles_router
from yp_api.interfaces.http.v1.devices import router as devices_router
from yp_api.interfaces.http.v1.streams import router as streams_router
from yp_api.interfaces.http.v1.dashboards import router as dashboards_router
from yp_api.interfaces.http.v1.analytics import router as analytics_router
from yp_api.interfaces.http.v1.automation import router as automation_router
from yp_api.interfaces.http.v1.fleets import router as fleets_router
from yp_api.interfaces.http.v1.firmwares import router as firmwares_router

router = APIRouter()

class ProjectResponse(BaseModel):
    id: str
    name: str
    organization_id: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

class ProjectListResponse(BaseModel):
    data: List[ProjectResponse]
    meta: dict = {}

class ProjectSingleResponse(BaseModel):
    data: ProjectResponse
    meta: dict = {}

class CreateProjectRequest(BaseModel):
    name: str
    organization_id: str
    description: Optional[str] = None

class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

@router.get("", response_model=ProjectListResponse)
async def list_projects(
    user: User = Depends(get_current_user),
    use_case: ListProjectsUseCase = Depends(get_list_projects_use_case)
):
    projects = await use_case.execute(user.id)
    return ProjectListResponse(
        data=[
            ProjectResponse(
                id=p.id, name=p.name, organization_id=p.org_id, description=p.description, created_at=p.created_at
            ) for p in projects
        ],
        meta={"page": {"has_more": False}}
    )

@router.post("", response_model=ProjectSingleResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest,
    user: User = Depends(get_current_user),
    use_case: CreateProjectUseCase = Depends(get_create_project_use_case)
):
    cmd = CreateProjectCommand(
        name=request.name,
        organization_id=request.organization_id,
        description=request.description
    )
    project = await use_case.execute(user.id, cmd)
    return ProjectSingleResponse(
        data=ProjectResponse(
            id=project.id, name=project.name, organization_id=project.org_id, description=project.description, created_at=project.created_at
        )
    )

@router.get("/{project_id}", response_model=ProjectSingleResponse, dependencies=[Depends(require_project_permission(ProjectPermission.PROJECT_VIEW))])
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    use_case: GetProjectUseCase = Depends(get_get_project_use_case)
):
    project = await use_case.execute(user.id, project_id)
    
    # Adding mock counters for data contracts
    response_data = ProjectResponse(
        id=project.id, name=project.name, organization_id=project.org_id, description=project.description, created_at=project.created_at
    ).model_dump()
    response_data["device_count"] = 0
    response_data["datapoints_24h"] = 0
    response_data["active_alerts"] = 0
    response_data["retention_days"] = 30
    
    return {"data": response_data, "meta": {}}

@router.patch("/{project_id}", response_model=ProjectSingleResponse, dependencies=[Depends(require_project_permission(ProjectPermission.PROJECT_UPDATE))])
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    user: User = Depends(get_current_user),
    use_case: UpdateProjectUseCase = Depends(get_update_project_use_case)
):
    cmd = UpdateProjectCommand(name=request.name, description=request.description)
    project = await use_case.execute(user.id, project_id, cmd)
    return ProjectSingleResponse(
        data=ProjectResponse(
            id=project.id, name=project.name, organization_id=project.org_id, description=project.description, created_at=project.created_at
        )
    )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_project_permission(ProjectPermission.PROJECT_DELETE))])
async def delete_project(
    project_id: str,
    user: User = Depends(get_current_user),
    use_case: DeleteProjectUseCase = Depends(get_delete_project_use_case)
):
    await use_case.execute(user.id, project_id)

router.include_router(device_profiles_router, prefix="/{project_id}/device-profiles", tags=["device-profiles"])
router.include_router(devices_router, prefix="/{project_id}/devices", tags=["devices"])
router.include_router(streams_router, prefix="/{project_id}/streams", tags=["streams"])
router.include_router(dashboards_router, prefix="/{project_id}/dashboards", tags=["dashboards"])
router.include_router(analytics_router, prefix="/{project_id}/analytics", tags=["analytics"])
router.include_router(automation_router, prefix="/{project_id}/automation", tags=["automation"])
router.include_router(fleets_router, prefix="/{project_id}/fleets", tags=["fleets"])
router.include_router(firmwares_router, prefix="/{project_id}/firmwares", tags=["firmwares"])
