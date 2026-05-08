from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

@dataclass
class Dashboard:
    id: str
    project_id: str
    name: str
    layout: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class DashboardRepository:
    async def get(self, id: str) -> Optional[Dashboard]: ...
    async def save(self, dashboard: Dashboard) -> None: ...
    async def list_by_project(self, project_id: str) -> List[Dashboard]: ...
    async def delete(self, id: str) -> None: ...
