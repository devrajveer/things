from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class Project(BaseModel):
    id: str
    org_id: str
    name: str
    slug: str
    description: Optional[str] = None
    deleted_at: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProjectMember(BaseModel):
    project_id: str
    user_id: str
    role: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
