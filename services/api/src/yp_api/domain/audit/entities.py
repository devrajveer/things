from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class AuditEvent(BaseModel):
    id: str
    action: str
    actor_id: Optional[str] = None
    target_id: Optional[str] = None
    data: Optional[dict] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
