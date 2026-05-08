from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from yp_api.domain.dashboards.entities import Dashboard
from yp_api.models.core import Dashboard as DashboardModel

class SQLDashboardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: str) -> Optional[Dashboard]:
        stmt = select(DashboardModel).where(DashboardModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            return self._to_entity(model)
        return None

    async def save(self, dashboard: Dashboard) -> Dashboard:
        stmt = select(DashboardModel).where(DashboardModel.id == dashboard.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.name = dashboard.name
            model.layout = dashboard.layout
            model.updated_at = dashboard.updated_at
        else:
            model = DashboardModel(
                id=dashboard.id,
                project_id=dashboard.project_id,
                name=dashboard.name,
                layout=dashboard.layout,
                created_at=dashboard.created_at,
                updated_at=dashboard.updated_at
            )
            self.session.add(model)
        
        return dashboard

    async def list_by_project(self, project_id: str) -> List[Dashboard]:
        stmt = select(DashboardModel).where(DashboardModel.project_id == project_id).order_by(DashboardModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete(self, id: str) -> None:
        stmt = delete(DashboardModel).where(DashboardModel.id == id)
        await self.session.execute(stmt)

    def _to_entity(self, model: DashboardModel) -> Dashboard:
        return Dashboard(
            id=model.id,
            project_id=model.project_id,
            name=model.name,
            layout=model.layout,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
