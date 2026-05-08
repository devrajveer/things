from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime
from yp_api.domain.users.entities import User
from yp_api.interfaces.http.dependencies import (
    get_current_user,
    get_uow
)
from yp_api.application.devices.list_streams import ListStreamsUseCase

router = APIRouter()

class StreamResponse(BaseModel):
    id: str
    device_id: str
    key: str
    value_type: str
    unit: Optional[str] = None
    display_name: Optional[str] = None
    last_value: Any = None
    last_value_at: Optional[datetime] = None
    created_at: datetime

class StreamListResponse(BaseModel):
    data: List[StreamResponse]
    meta: dict = {}

@router.get("", response_model=StreamListResponse)
async def list_streams(
    project_id: str,
    device_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    use_case = ListStreamsUseCase(uow)
    streams = await use_case.execute(user.id, project_id, device_id=device_id)
    return {
        "data": [
            StreamResponse(
                id=s.id,
                device_id=s.device_id,
                key=s.key,
                value_type=s.value_type,
                unit=s.unit,
                display_name=s.display_name,
                last_value=s.last_value,
                last_value_at=s.last_value_at,
                created_at=s.created_at
            ) for s in streams
        ]
    }
