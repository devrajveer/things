from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from yp_api.domain.users.entities import User
from yp_api.interfaces.http.dependencies import get_current_user, get_uow
from yp_api.domain.dashboards.entities import Dashboard
import uuid

router = APIRouter()

class DashboardResponse(BaseModel):
    id: str
    name: str
    layout: Dict[str, Any]

class CreateDashboardRequest(BaseModel):
    name: str
    layout: Optional[Dict[str, Any]] = {}

@router.get("", response_model=List[DashboardResponse])
async def list_dashboards(
    project_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        dashboards = await uow.dashboards.list_by_project(project_id)
        return [
            DashboardResponse(id=d.id, name=d.name, layout=d.layout)
            for d in dashboards
        ]

@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    project_id: str,
    request: CreateDashboardRequest,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        dashboard = Dashboard(
            id=f"dsb_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            name=request.name,
            layout=request.layout
        )
        await uow.dashboards.save(dashboard)
        await uow.commit()
        return DashboardResponse(id=dashboard.id, name=dashboard.name, layout=dashboard.layout)

@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    project_id: str,
    dashboard_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        dashboard = await uow.dashboards.get(dashboard_id)
        if not dashboard or dashboard.project_id != project_id:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return DashboardResponse(id=dashboard.id, name=dashboard.name, layout=dashboard.layout)

@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    project_id: str,
    dashboard_id: str,
    request: CreateDashboardRequest,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        dashboard = await uow.dashboards.get(dashboard_id)
        if not dashboard or dashboard.project_id != project_id:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        dashboard.name = request.name
        dashboard.layout = request.layout
        await uow.dashboards.save(dashboard)
        await uow.commit()
        return DashboardResponse(id=dashboard.id, name=dashboard.name, layout=dashboard.layout)

@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    project_id: str,
    dashboard_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        await uow.dashboards.delete(dashboard_id)
        await uow.commit()
